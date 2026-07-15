from ctf.models import Mission, MissionCategory, MissionTag, UserMissionProgress

from adminapi.serializers.ctf import (
    CtfMissionAdminSerializer,
    CtfMissionProgressAdminSerializer,
    MissionCategoryAdminSerializer,
    MissionTagAdminSerializer,
)

from .base import AdminModelViewSet
from .progress import ReadOnlyAdminViewSet


class CtfMissionAdminViewSet(AdminModelViewSet):
    queryset = Mission.objects.select_related("category", "writeup").prefetch_related("tags").all()
    serializer_class = CtfMissionAdminSerializer
    filterset_fields = ["difficulty", "status", "category", "tags"]
    search_fields = ["title", "short_description"]
    ordering_fields = ["id", "title", "points", "created_at"]
    bulk_toggle_field = None


class MissionCategoryAdminViewSet(AdminModelViewSet):
    queryset = MissionCategory.objects.all()
    serializer_class = MissionCategoryAdminSerializer
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "id"]
    bulk_toggle_field = None


class MissionTagAdminViewSet(AdminModelViewSet):
    queryset = MissionTag.objects.all()
    serializer_class = MissionTagAdminSerializer
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "id"]
    bulk_toggle_field = None


class CtfMissionProgressAdminViewSet(ReadOnlyAdminViewSet):
    queryset = UserMissionProgress.objects.select_related("user", "mission").all()
    serializer_class = CtfMissionProgressAdminSerializer
    filterset_fields = ["user", "mission", "status"]
    search_fields = ["user__username", "mission__title"]
    ordering_fields = ["solved_at", "writeup_unlocked_at"]
