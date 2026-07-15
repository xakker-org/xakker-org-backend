from rest_framework import serializers

from chatbot.models import AssistantPromptNote, AssistantPromptSettings


class AssistantPromptSettingsAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantPromptSettings
        fields = ["base_prompt_az", "base_prompt_en", "updated_at"]
        read_only_fields = ["updated_at"]


class AssistantPromptNoteAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantPromptNote
        fields = ["id", "title", "content", "lang", "is_active", "order", "created_at", "updated_at"]
