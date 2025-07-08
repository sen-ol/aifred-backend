from django.db import models
from django.conf import settings

class Advisor(models.Model):
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=100)
    system_prompt = models.TextField()
    image_url = models.URLField(blank=True)

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    advisor = models.ForeignKey(Advisor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
