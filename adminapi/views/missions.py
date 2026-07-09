from courses.models import Mission, MissionExam, MissionExamQuestion, MissionPass

from adminapi.serializers.missions import (
    MissionAdminSerializer,
    MissionExamAdminSerializer,
    MissionExamQuestionAdminSerializer,
    MissionPassAdminSerializer,
)

from .base import AdminModelViewSet


class MissionAdminViewSet(AdminModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionAdminSerializer
    filterset_fields = ["is_published", "difficulty"]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "id", "title", "xp_reward"]


class MissionExamAdminViewSet(AdminModelViewSet):
    queryset = MissionExam.objects.select_related("mission").all()
    serializer_class = MissionExamAdminSerializer
    filterset_fields = ["is_published", "mission"]
    search_fields = ["title", "mission__title"]
    ordering_fields = ["id"]


class MissionPassAdminViewSet(AdminModelViewSet):
    queryset = MissionPass.objects.select_related("mission").all()
    serializer_class = MissionPassAdminSerializer
    filterset_fields = ["mission", "is_published"]
    search_fields = ["title", "mission__title"]
    ordering_fields = ["order", "id"]


class MissionExamQuestionAdminViewSet(AdminModelViewSet):
    queryset = MissionExamQuestion.objects.select_related("exam").prefetch_related("choices").all()
    serializer_class = MissionExamQuestionAdminSerializer
    filterset_fields = ["exam", "question_type"]
    search_fields = ["question_text"]
    ordering_fields = ["order", "id"]
    bulk_toggle_field = None
