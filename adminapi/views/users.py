from django.contrib.auth.models import User
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Activity

from adminapi.models import AdminAuditLog
from adminapi.pagination import AdminPagination
from adminapi.permissions import IsStaffUser, IsSuperUser
from adminapi.serializers.users import AdminUserSerializer, AwardXpSerializer, ToggleSerializer


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.select_related("profile").all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [IsStaffUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "is_staff", "is_superuser"]
    search_fields = ["username", "email", "profile__full_name"]
    ordering_fields = ["date_joined", "id", "profile__xp"]

    def _log(self, action_name, instance, changes=None):
        AdminAuditLog.objects.create(
            actor=self.request.user,
            action=action_name,
            model_label="auth.User",
            object_id=str(instance.pk),
            changes=changes,
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log(AdminAuditLog.Action.UPDATE, instance)

    def _respond(self, user):
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        user = self.get_object()
        serializer = ToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = serializer.validated_data["value"]
        user.save(update_fields=["is_active"])
        self._log(AdminAuditLog.Action.ACTION, user, {"action": "set_active", "value": user.is_active})
        return self._respond(user)

    @action(detail=True, methods=["post"], permission_classes=[IsSuperUser])
    def set_staff(self, request, pk=None):
        user = self.get_object()
        serializer = ToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_staff = serializer.validated_data["value"]
        user.save(update_fields=["is_staff"])
        self._log(AdminAuditLog.Action.ACTION, user, {"action": "set_staff", "value": user.is_staff})
        return self._respond(user)

    @action(detail=True, methods=["post"])
    def award_xp(self, request, pk=None):
        user = self.get_object()
        serializer = AwardXpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        with transaction.atomic():
            user.profile.award_xp(amount)
            Activity.objects.create(
                user=user,
                kind=Activity.Kind.ADMIN_GRANT,
                title="XP admin tərəfindən verildi",
                detail=f"+{amount} XP",
                xp_delta=amount,
            )
        self._log(AdminAuditLog.Action.ACTION, user, {"action": "award_xp", "amount": amount})
        return self._respond(user)

    @action(detail=True, methods=["post"])
    def reset_streak(self, request, pk=None):
        user = self.get_object()
        user.profile.streak_days = 0
        user.profile.save(update_fields=["streak_days"])
        self._log(AdminAuditLog.Action.ACTION, user, {"action": "reset_streak"})
        return self._respond(user)
