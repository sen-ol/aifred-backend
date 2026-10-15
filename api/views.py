import logging

from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from openai import APIError, OpenAI
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import Advisor, Conversation, Message
from .serializers import AdvisorSerializer, ChatRequestSerializer, MessageSerializer

logger = logging.getLogger(__name__)


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "service": "aifred-api"})


class AdvisorList(generics.ListAPIView):
    queryset = Advisor.objects.all()
    serializer_class = AdvisorSerializer
    permission_classes = [permissions.AllowAny]


class ChatView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request, slug):
        payload = ChatRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        advisor = get_object_or_404(Advisor, pk=slug)
        convo_id = payload.validated_data.get("conversation_id")
        convo = None

        if convo_id:
            if not request.user.is_authenticated:
                return Response({"detail": "Bu sohbet için giriş yapmalısınız."}, status=401)
            convo = get_object_or_404(
                Conversation, id=convo_id, user=request.user, advisor=advisor
            )

        if not settings.OPENAI_API_KEY:
            return Response(
                {"detail": "Sohbet servisi henüz yapılandırılmadı."}, status=503
            )

        history = []
        if convo:
            recent = list(convo.messages.order_by("-created_at", "-id")[:20])
            history.extend(
                {"role": message.role, "content": message.content}
                for message in reversed(recent)
            )
        elif not request.user.is_authenticated:
            history.extend(payload.validated_data.get("history", []))
        text = payload.validated_data["message"]
        history.append({"role": "user", "content": text})

        try:
            with OpenAI(api_key=settings.OPENAI_API_KEY, timeout=25.0, max_retries=0) as client:
                completion = client.responses.create(
                    model=settings.OPENAI_MODEL,
                    instructions=advisor.system_prompt,
                    input=history,
                    reasoning={"effort": settings.OPENAI_REASONING_EFFORT},
                    max_output_tokens=1200,
                    store=False,
                )
            reply = (completion.output_text or "").strip()
        except APIError as exc:
            # Log only recognized codes, never provider messages or request bodies.
            known_codes = {
                "insufficient_quota", "credit_balance_exhausted",
                "organization_spend_limit_exceeded", "project_spend_limit_exceeded",
                "organization_usage_limit_exceeded", "rate_limit_exceeded", "slow_down",
                "model_not_found", "invalid_api_key",
            }
            code = getattr(exc, "code", None)
            logger.warning(
                "AI provider failed: %s code=%s status=%s",
                type(exc).__name__, code if isinstance(code, str) and code in known_codes else "unknown",
                getattr(exc, "status_code", None),
            )
            return Response(
                {"detail": "Yanıt şu anda üretilemiyor. Lütfen tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not reply:
            return Response({"detail": "Boş yanıt alındı. Lütfen tekrar deneyin."}, status=502)

        if request.user.is_authenticated:
            with transaction.atomic():
                if convo is None:
                    convo = Conversation.objects.create(user=request.user, advisor=advisor)
                Message.objects.create(conversation=convo, role="user", content=text)
                Message.objects.create(conversation=convo, role="assistant", content=reply)
            return Response({
                "conversation_id": convo.id,
                "reply": reply,
                "messages": MessageSerializer(
                    convo.messages.order_by("created_at", "id"), many=True
                ).data,
            })
        return Response({"reply": reply})
