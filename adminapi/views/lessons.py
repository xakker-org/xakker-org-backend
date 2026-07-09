from courses.models import Lesson, LessonQuestion

from adminapi.serializers.lessons import LessonAdminSerializer, LessonQuestionAdminSerializer

from .base import AdminModelViewSet


class LessonAdminViewSet(AdminModelViewSet):
    queryset = Lesson.objects.select_related("course").all()
    serializer_class = LessonAdminSerializer
    filterset_fields = ["course"]
    search_fields = ["title", "content"]
    ordering_fields = ["order", "id"]
    bulk_toggle_field = None


class LessonQuestionAdminViewSet(AdminModelViewSet):
    queryset = LessonQuestion.objects.select_related("lesson").prefetch_related("choices").all()
    serializer_class = LessonQuestionAdminSerializer
    filterset_fields = ["lesson"]
    search_fields = ["text"]
    ordering_fields = ["order", "id", "points"]
    bulk_toggle_field = None
