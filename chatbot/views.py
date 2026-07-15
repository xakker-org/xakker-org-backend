from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message, MessageRole
from .providers.base import ProviderError
from .serializers import (
    ChatMessageRequestSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    MessageSerializer,
)
from .services import generate_reply


def _title_from_message(message: str) -> str:
    trimmed = message.strip()
    return trimmed[:48] + ("…" if len(trimmed) > 48 else "")


class ChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        conversation_id = payload.get("conversation_id")
        message_text = payload["message"]
        lang = payload.get("lang", "az")

        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
            if conversation.user_id != request.user.id:
                return Response({"detail": "You do not have access to this conversation."}, status=status.HTTP_403_FORBIDDEN)
        else:
            conversation = Conversation.objects.create(
                user=request.user, title=_title_from_message(message_text)
            )

        with transaction.atomic():
            user_message = Message.objects.create(
                conversation=conversation, role=MessageRole.USER, content=message_text
            )

            try:
                reply_text = generate_reply(conversation, lang)
            except ProviderError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            assistant_message = Message.objects.create(
                conversation=conversation, role=MessageRole.ASSISTANT, content=reply_text
            )
            conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "conversation_id": conversation.id,
                "title": conversation.title,
                "user_message": MessageSerializer(user_message).data,
                "assistant_message": MessageSerializer(assistant_message).data,
            },
            status=status.HTTP_200_OK,
        )


class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user).prefetch_related("messages")
        return Response(ConversationListSerializer(conversations, many=True).data)


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            conversation = Conversation.objects.prefetch_related("messages").get(id=id)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        if conversation.user_id != request.user.id:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ConversationDetailSerializer(conversation).data)

    def delete(self, request, id):
        try:
            conversation = Conversation.objects.get(id=id)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        if conversation.user_id != request.user.id:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
