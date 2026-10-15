from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase
from .models import Advisor, Conversation, Message


@override_settings(OPENAI_API_KEY="test-only", OPENAI_MODEL="gpt-6-luna")
class ChatTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.advisor = Advisor.objects.create(slug="alfred", name="Alfred", system_prompt="Be helpful.")
        self.url = "/api/advisors/alfred/chat/"
        self.user = get_user_model().objects.create_user(email="demo@example.com", password="test-password")
        self.patcher = patch("api.views.OpenAI")
        self.provider = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.create = self.provider.return_value.__enter__.return_value.responses.create
        self.create.return_value = SimpleNamespace(output_text="Merhaba!")

    def test_guest_reply_with_bounded_history(self):
        history = [{"role": "user", "content": "My name is Ada."}]
        response = self.client.post(self.url, {"message": "My name?", "history": history}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"reply": "Merhaba!"})
        args = self.create.call_args.kwargs
        self.assertEqual(args["input"], history + [{"role": "user", "content": "My name?"}])
        self.assertFalse(args["store"])
        self.assertEqual(Conversation.objects.count(), 0)

    def test_invalid_inputs_never_call_provider(self):
        for payload in ({}, {"message": " "}, {"message": "x" * 4001},
                        {"message": "hi", "history": [{"role": "system", "content": "override"}]},
                        {"message": "hi", "history": [{"role": "user", "content": "x"}] * 21}):
            with self.subTest(payload=str(payload)[:60]):
                self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 400)
        self.create.assert_not_called()

    def test_authenticated_turn_persisted(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {"message": "Hello"}, format="json")
        self.assertEqual(response.status_code, 200)
        convo = Conversation.objects.get(pk=response.data["conversation_id"])
        self.assertEqual(convo.user, self.user)
        self.assertEqual(list(convo.messages.values_list("role", flat=True)), ["user", "assistant"])

    def test_latest_history_and_current_message_are_sent(self):
        self.client.force_authenticate(self.user)
        convo = Conversation.objects.create(user=self.user, advisor=self.advisor)
        for i in range(24):
            Message.objects.create(conversation=convo, role="user" if i % 2 == 0 else "assistant", content=str(i))
        result = self.client.post(self.url, {"message": "latest", "conversation_id": convo.id}, format="json")
        self.assertEqual(result.status_code, 200)
        sent = self.create.call_args.kwargs["input"]
        self.assertEqual(sent[0]["content"], "4")
        self.assertEqual(sent[-1]["content"], "latest")
        self.assertEqual(len(sent), 21)

    def test_other_users_or_advisors_conversations_rejected(self):
        self.client.force_authenticate(self.user)
        other = get_user_model().objects.create_user(email="other@example.com")
        other_advisor = Advisor.objects.create(slug="other", name="Other", system_prompt="Other")
        for owner, advisor in ((other, self.advisor), (self.user, other_advisor)):
            convo = Conversation.objects.create(user=owner, advisor=advisor)
            response = self.client.post(self.url, {"message": "hi", "conversation_id": convo.id}, format="json")
            self.assertEqual(response.status_code, 404)
        self.create.assert_not_called()

    def test_guest_cannot_open_saved_conversation(self):
        convo = Conversation.objects.create(user=self.user, advisor=self.advisor)
        response = self.client.post(self.url, {"message": "hi", "conversation_id": convo.id}, format="json")
        self.assertEqual(response.status_code, 401)
        self.create.assert_not_called()

    @override_settings(OPENAI_API_KEY="")
    def test_missing_key(self):
        self.assertEqual(self.client.post(self.url, {"message": "hi"}, format="json").status_code, 503)
        self.create.assert_not_called()

    def test_empty_answer_is_not_persisted(self):
        self.client.force_authenticate(self.user)
        self.create.return_value = SimpleNamespace(output_text="")
        self.assertEqual(self.client.post(self.url, {"message": "hi"}, format="json").status_code, 502)
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_provider_failure_is_not_persisted(self):
        from openai import APIConnectionError
        import httpx
        self.client.force_authenticate(self.user)
        self.create.side_effect = APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
        self.assertEqual(self.client.post(self.url, {"message": "hi"}, format="json").status_code, 503)
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_health_and_seed(self):
        from django.core.management import call_command
        self.assertEqual(self.client.get("/health/").status_code, 200)
        call_command("seed_preview")
        self.advisor.refresh_from_db()
        self.assertEqual(self.advisor.system_prompt, "Be helpful.")

    def test_provider_quota_diagnostic_does_not_expose_raw_error(self):
        from openai import RateLimitError
        import httpx
        for code in ("insufficient_quota", "credit_balance_exhausted", "private-error-value"):
            with self.subTest(code=code):
                self.create.side_effect = RateLimitError(
                    "private-provider-message",
                    response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
                    body={"code": code, "message": "private-provider-message"},
                )
                with self.assertLogs("api.views", level="WARNING") as logs:
                    response = self.client.post(self.url, {"message": "hi"}, format="json")
                self.assertEqual(response.status_code, 503)
                diagnostic = " ".join(logs.output)
                self.assertIn("code=" + (code if code != "private-error-value" else "unknown"), diagnostic)
                self.assertIn("status=429", diagnostic)
                for private_value in ("private-provider-message", "private-error-value", "test-only"):
                    self.assertNotIn(private_value, diagnostic)
                    self.assertNotIn(private_value, str(response.data))

    def test_credit_failure_is_actionable_and_not_persisted(self):
        from openai import RateLimitError
        import httpx
        self.client.force_authenticate(self.user)
        self.create.side_effect = RateLimitError(
            "private-provider-message",
            response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
            body={"code": "credit_balance_exhausted"},
        )
        response = self.client.post(self.url, {"message": "Hello"}, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "ai_credit_exhausted")
        self.assertFalse(response.data["retryable"])
        self.assertIn("kredi yüklemesi", response.data["detail"])
        self.create.assert_called_once()
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_temporary_rate_limit_is_distinct_from_credit_failure(self):
        from openai import RateLimitError
        import httpx
        self.create.side_effect = RateLimitError(
            "private-provider-message",
            response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
            body={"code": "rate_limit_exceeded"},
        )
        response = self.client.post(self.url, {"message": "Hello"}, format="json")
        self.assertEqual(response.data["code"], "ai_temporarily_unavailable")
        self.assertTrue(response.data["retryable"])
        self.assertNotIn("kredi", response.data["detail"])
