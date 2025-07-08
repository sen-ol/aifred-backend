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

class GuestProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="guest_profile")
    passport_no   = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

class StaffProfile(models.Model):
    user  = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="staff_profile")
    title = models.CharField(max_length=80, blank=True)
    desk  = models.CharField(max_length=80, blank=True)

