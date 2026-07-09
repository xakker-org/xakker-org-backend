from courses.models import LearningPlan

from adminapi.serializers.plans import LearningPlanAdminSerializer

from .base import AdminModelViewSet


class LearningPlanAdminViewSet(AdminModelViewSet):
    queryset = LearningPlan.objects.prefetch_related("learningplancourse_set__course").all()
    serializer_class = LearningPlanAdminSerializer
    filterset_fields = ["is_published", "is_featured", "level"]
    search_fields = ["title", "summary", "description"]
    ordering_fields = ["id", "title", "estimated_hours"]
