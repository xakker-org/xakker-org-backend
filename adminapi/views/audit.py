from adminapi.models import AdminAuditLog
from adminapi.serializers.audit import AdminAuditLogSerializer

from .progress import ReadOnlyAdminViewSet


class AdminAuditLogViewSet(ReadOnlyAdminViewSet):
    queryset = AdminAuditLog.objects.select_related("actor").all()
    serializer_class = AdminAuditLogSerializer
    filterset_fields = ["actor", "action", "model_label"]
    search_fields = ["model_label", "object_id"]
    ordering_fields = ["created_at"]
