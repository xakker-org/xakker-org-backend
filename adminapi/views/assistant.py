from rest_framework.generics import RetrieveUpdateAPIView

from chatbot.models import AssistantPromptNote, AssistantPromptSettings

from adminapi.models import AdminAuditLog
from adminapi.permissions import IsStaffUser
from adminapi.serializers.assistant import (
    AssistantPromptNoteAdminSerializer,
    AssistantPromptSettingsAdminSerializer,
)

from .base import AdminModelViewSet


class AssistantPromptSettingsView(RetrieveUpdateAPIView):
    """Singleton base system prompt (az/en) — GET/PUT/PATCH."""

    permission_classes = [IsStaffUser]
    serializer_class = AssistantPromptSettingsAdminSerializer

    def get_object(self):
        return AssistantPromptSettings.load()

    def perform_update(self, serializer):
        instance = serializer.save()
        user = getattr(self.request, "user", None)
        AdminAuditLog.objects.create(
            actor=user if user and user.is_authenticated else None,
            action=AdminAuditLog.Action.UPDATE,
            model_label=AssistantPromptSettings._meta.label,
            object_id=str(instance.pk),
        )


class AssistantPromptNoteAdminViewSet(AdminModelViewSet):
    queryset = AssistantPromptNote.objects.all().order_by("order", "id")
    serializer_class = AssistantPromptNoteAdminSerializer
    search_fields = ["title", "content"]
    filterset_fields = ["is_active", "lang"]
    ordering_fields = ["order", "id", "title"]
    bulk_toggle_field = "is_active"
