from courses.models import Task, TaskQuestion

from adminapi.serializers.tasks import TaskAdminSerializer, TaskQuestionAdminSerializer

from .base import AdminModelViewSet


class TaskAdminViewSet(AdminModelViewSet):
    queryset = Task.objects.select_related("room").all()
    serializer_class = TaskAdminSerializer
    filterset_fields = ["room"]
    search_fields = ["title", "content"]
    ordering_fields = ["order", "id", "points"]
    bulk_toggle_field = None


class TaskQuestionAdminViewSet(AdminModelViewSet):
    queryset = TaskQuestion.objects.select_related("task").prefetch_related("choices").all()
    serializer_class = TaskQuestionAdminSerializer
    filterset_fields = ["task", "kind"]
    search_fields = ["prompt", "answer"]
    ordering_fields = ["order", "id", "points"]
    bulk_toggle_field = None
