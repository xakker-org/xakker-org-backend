from rest_framework import serializers

from adminapi.models import AdminAuditLog


class AdminAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True, default=None)

    class Meta:
        model = AdminAuditLog
        fields = ["id", "actor", "actor_username", "action", "model_label", "object_id", "changes", "created_at"]
