from courses.models import Category, Course, Room, RoomTag

from adminapi.serializers.content import (
    CategoryAdminSerializer,
    CourseAdminSerializer,
    RoomAdminSerializer,
    RoomTagAdminSerializer,
)

from .base import AdminModelViewSet


class CategoryAdminViewSet(AdminModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategoryAdminSerializer
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]
    bulk_toggle_field = None


class RoomTagAdminViewSet(AdminModelViewSet):
    queryset = RoomTag.objects.all().order_by("name")
    serializer_class = RoomTagAdminSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    bulk_toggle_field = None


class CourseAdminViewSet(AdminModelViewSet):
    queryset = Course.objects.select_related("category").all().order_by("id")
    serializer_class = CourseAdminSerializer
    filterset_fields = ["is_published", "category"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "id"]


class RoomAdminViewSet(AdminModelViewSet):
    queryset = Room.objects.select_related("course").prefetch_related("tags").all()
    serializer_class = RoomAdminSerializer
    filterset_fields = ["is_published", "is_premium", "level", "env", "course"]
    search_fields = ["title", "summary", "description", "target_ip"]
    ordering_fields = ["order", "id", "title", "points"]
