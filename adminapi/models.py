from django.conf import settings
from django.db import models


class AdminAuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        BULK = "bulk", "Bulk action"
        ACTION = "action", "Custom action"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_audit_logs",
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    model_label = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64, blank=True, default="")
    changes = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        who = self.actor.username if self.actor else "?"
        return f"{who} · {self.action} · {self.model_label} #{self.object_id}"
