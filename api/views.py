import os, openai
from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Advisor, Conversation, Message
from .serializers import AdvisorSerializer, MessageSerializer

class AdvisorList(generics.ListAPIView):
    queryset = Advisor.objects.all()
    serializer_class = AdvisorSerializer
    permission_classes = [permissions.AllowAny]

class ChatView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, slug):
        advisor = get_object_or_404(Advisor, pk=slug)
        user = request.user if request.user.is_authenticated else None
        if user:
            convo_id = request.data.get("conversation_id")
            convo = (
                get_object_or_404(Conversation, id=convo_id, user=user)
                if convo_id else Conversation.objects.create(user=user, advisor=advisor)
            )
            Message.objects.create(conversation=convo, role="user",
                                   content=request.data["message"])
        else:
            convo = None
            history = [{"role":"system","content":advisor.system_prompt},
                       {"role":"user","content":request.data["message"]}]

        
        history = [{"role":"system","content":advisor.system_prompt}] + [
            {"role":m.role,"content":m.content} for m in convo.messages.order_by("created_at")[:20]
        ]
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=history,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        bot_text = completion.choices[0].message.content.strip()
        
        if convo:
            Message.objects.create(conversation=convo, role="assistant", content=bot_text)
            msgs = MessageSerializer(convo.messages.all(), many=True).data
            return Response({"conversation_id": convo.id, "reply": bot_text,
                             "messages": msgs}, status=status.HTTP_200_OK)
        else:
            return Response({"reply": bot_text}, status=status.HTTP_200_OK)
