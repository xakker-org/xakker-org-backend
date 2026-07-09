from courses.models import Question

from adminapi.serializers.questions import QuestionAdminSerializer

from .base import AdminModelViewSet


class QuestionAdminViewSet(AdminModelViewSet):
    queryset = Question.objects.select_related("course").all()
    serializer_class = QuestionAdminSerializer
    filterset_fields = ["course", "question_type", "level"]
    search_fields = ["title", "prompt", "expected_answer"]
    ordering_fields = ["order", "id", "points"]
    bulk_toggle_field = None
