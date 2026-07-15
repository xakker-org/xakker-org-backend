from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from courses.models import (
    Enrollment,
    MissionExamAttempt,
    MissionProgress,
    UserLessonProgress,
    UserQuestionAttempt,
    UserTaskProgress,
)

from adminapi.pagination import AdminPagination
from adminapi.permissions import IsStaffUser
from adminapi.serializers.progress import (
    EnrollmentAdminSerializer,
    MissionExamAttemptAdminSerializer,
    MissionProgressAdminSerializer,
    UserLessonProgressAdminSerializer,
    UserQuestionAttemptAdminSerializer,
    UserTaskProgressAdminSerializer,
)


class ReadOnlyAdminViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsStaffUser]
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


class UserTaskProgressAdminViewSet(ReadOnlyAdminViewSet):
    queryset = UserTaskProgress.objects.select_related("user", "task", "task__room").all()
    serializer_class = UserTaskProgressAdminSerializer
    filterset_fields = ["user", "task__room", "completed"]
    search_fields = ["user__username", "task__title"]
    ordering_fields = ["updated_at", "completed_at"]


class UserQuestionAttemptAdminViewSet(ReadOnlyAdminViewSet):
    queryset = UserQuestionAttempt.objects.select_related("user", "question").all()
    serializer_class = UserQuestionAttemptAdminSerializer
    filterset_fields = ["user", "is_correct"]
    search_fields = ["user__username", "question__prompt"]
    ordering_fields = ["attempted_at"]


class UserLessonProgressAdminViewSet(ReadOnlyAdminViewSet):
    queryset = UserLessonProgress.objects.select_related("user", "lesson").all()
    serializer_class = UserLessonProgressAdminSerializer
    filterset_fields = ["user", "lesson", "is_completed"]
    search_fields = ["user__username", "lesson__title"]
    ordering_fields = ["completed_at"]


class MissionProgressAdminViewSet(ReadOnlyAdminViewSet):
    queryset = MissionProgress.objects.select_related("user", "mission").all()
    serializer_class = MissionProgressAdminSerializer
    filterset_fields = ["user", "mission", "is_completed", "exam_passed"]
    search_fields = ["user__username", "mission__title"]
    ordering_fields = ["started_at", "completed_at"]


class MissionExamAttemptAdminViewSet(ReadOnlyAdminViewSet):
    queryset = MissionExamAttempt.objects.select_related("user", "exam").all()
    serializer_class = MissionExamAttemptAdminSerializer
    filterset_fields = ["user", "exam", "passed"]
    search_fields = ["user__username", "exam__title"]
    ordering_fields = ["started_at", "submitted_at", "score"]


class EnrollmentAdminViewSet(ReadOnlyAdminViewSet):
    queryset = Enrollment.objects.select_related("user", "course").all()
    serializer_class = EnrollmentAdminSerializer
    filterset_fields = ["user", "course"]
    search_fields = ["user__username", "course__title"]
    ordering_fields = ["created_at"]
