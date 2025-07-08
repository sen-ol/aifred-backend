from django.contrib import admin
from .models import Advisor, Conversation, Message, GuestProfile, StaffProfile


@admin.register(Advisor)
class AdvisorAdmin(admin.ModelAdmin):
    list_display = ("slug", "name")
    search_fields = ("slug", "name")
    readonly_fields = ("slug",)   


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "advisor", "created_at")
    list_filter = ("advisor", "created_at")
    search_fields = ("user__email",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("conversation__id", "content")
    ordering = ("-created_at",)


# Profil modelleri opsiyonel – ekle / çıkar:
@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "passport_no", "date_of_birth")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "desk")
