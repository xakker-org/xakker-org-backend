from django.urls import path

from .views import ChatMessageView, ConversationDetailView, ConversationListView

urlpatterns = [
    path("message", ChatMessageView.as_view(), name="chatbot-message"),
    path("conversations", ConversationListView.as_view(), name="chatbot-conversation-list"),
    path("conversations/<int:id>", ConversationDetailView.as_view(), name="chatbot-conversation-detail"),
]
