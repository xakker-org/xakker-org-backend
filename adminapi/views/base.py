from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from adminapi.models import AdminAuditLog
from adminapi.pagination import AdminPagination
from adminapi.permissions import IsStaffUser


class AuditLogMixin:
    """Writes one AdminAuditLog row per create/update/delete/bulk action."""

    def _log(self, action_name, instance=None, object_id="", changes=None):
        user = getattr(self.request, "user", None)
        AdminAuditLog.objects.create(
            actor=user if user and user.is_authenticated else None,
            action=action_name,
            model_label=self.get_queryset().model._meta.label,
            object_id=str(object_id or (instance.pk if instance else "")),
            changes=changes,
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self._log(AdminAuditLog.Action.CREATE, instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log(AdminAuditLog.Action.UPDATE, instance)

    def perform_destroy(self, instance):
        object_id = instance.pk
        instance.delete()
        self._log(AdminAuditLog.Action.DELETE, object_id=object_id)


class BulkActionMixin:
    """POST {basePath}/bulk/ {action: "publish"|"unpublish"|"delete", ids: [...]}.

    `bulk_toggle_field` names the boolean field publish/unpublish acts on
    (usually "is_published"); set to None on viewsets whose model has no
    such field to disable those two actions (delete still works).
    """

    bulk_toggle_field = "is_published"

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        action_name = request.data.get("action")
        ids = request.data.get("ids") or []
        if not isinstance(ids, list) or not ids:
            return Response({"detail": "ids siyahısı tələb olunur."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(id__in=ids)

        if action_name == "delete":
            count = queryset.count()
            queryset.delete()
            self._log(
                AdminAuditLog.Action.BULK,
                object_id=",".join(map(str, ids)),
                changes={"action": "delete", "count": count},
            )
            return Response({"deleted": count})

        if action_name in ("publish", "unpublish") and self.bulk_toggle_field:
            value = action_name == "publish"
            count = queryset.update(**{self.bulk_toggle_field: value})
            self._log(
                AdminAuditLog.Action.BULK,
                object_id=",".join(map(str, ids)),
                changes={"action": action_name, "count": count},
            )
            return Response({"updated": count})

        return Response({"detail": "Naməlum əməliyyat."}, status=status.HTTP_400_BAD_REQUEST)


class AdminModelViewSet(AuditLogMixin, BulkActionMixin, viewsets.ModelViewSet):
    permission_classes = [IsStaffUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
