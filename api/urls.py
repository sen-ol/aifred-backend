from django.urls import path
from .views import AdvisorList, ChatView
urlpatterns = [
    path("advisors/", AdvisorList.as_view()),
    path("advisors/<slug:slug>/chat/", ChatView.as_view()),
]
