from rest_framework import serializers
from .models import Advisor, Message

class AdvisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advisor
        fields = ("slug", "name", "image_url")

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("role", "content", "created_at")



class HistoryMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=("user", "assistant"))
    content = serializers.CharField(max_length=4000)


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    history = HistoryMessageSerializer(many=True, required=False, max_length=20)
