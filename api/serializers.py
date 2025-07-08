from rest_framework import serializers
from .models import Advisor, Message

class AdvisorSerializer(serializers.ModelSerializer):
    class Meta: model=Advisor; fields=("slug","name","image_url")

class MessageSerializer(serializers.ModelSerializer):
    class Meta: model=Message; fields=("role","content","created_at")
