from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from adminapi.auth.views import AdminMeView, AdminTokenObtainPairView
from adminapi.views.analytics import AnalyticsActivityView, AnalyticsContentView, AnalyticsOverviewView
from adminapi.views.assistant import AssistantPromptNoteAdminViewSet, AssistantPromptSettingsView
from adminapi.views.audit import AdminAuditLogViewSet
from adminapi.views.content import (
    CategoryAdminViewSet,
    CourseAdminViewSet,
    RoomAdminViewSet,
    RoomTagAdminViewSet,
)
from adminapi.views.lessons import LessonAdminViewSet, LessonQuestionAdminViewSet
from adminapi.views.missions import (
    MissionAdminViewSet,
    MissionExamAdminViewSet,
    MissionExamQuestionAdminViewSet,
    MissionPassAdminViewSet,
)
from adminapi.views.plans import LearningPlanAdminViewSet
from adminapi.views.progress import (
    EnrollmentAdminViewSet,
    MissionExamAttemptAdminViewSet,
    MissionProgressAdminViewSet,
    UserLessonProgressAdminViewSet,
    UserQuestionAttemptAdminViewSet,
    UserTaskProgressAdminViewSet,
)
from adminapi.views.tasks import TaskAdminViewSet, TaskQuestionAdminViewSet
from adminapi.views.users import AdminUserViewSet

router = DefaultRouter()
router.register("categories", CategoryAdminViewSet, basename="admin-category")
router.register("room-tags", RoomTagAdminViewSet, basename="admin-roomtag")
router.register("courses", CourseAdminViewSet, basename="admin-course")
router.register("rooms", RoomAdminViewSet, basename="admin-room")
router.register("tasks", TaskAdminViewSet, basename="admin-task")
router.register("task-questions", TaskQuestionAdminViewSet, basename="admin-taskquestion")
router.register("lessons", LessonAdminViewSet, basename="admin-lesson")
router.register("lesson-questions", LessonQuestionAdminViewSet, basename="admin-lessonquestion")
router.register("plans", LearningPlanAdminViewSet, basename="admin-plan")
router.register("missions", MissionAdminViewSet, basename="admin-mission")
router.register("mission-passes", MissionPassAdminViewSet, basename="admin-missionpass")
router.register("mission-exams", MissionExamAdminViewSet, basename="admin-missionexam")
router.register("mission-exam-questions", MissionExamQuestionAdminViewSet, basename="admin-missionexamquestion")
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("progress/tasks", UserTaskProgressAdminViewSet, basename="admin-progress-task")
router.register("progress/task-question-attempts", UserQuestionAttemptAdminViewSet, basename="admin-progress-taskqa")
router.register("progress/lessons", UserLessonProgressAdminViewSet, basename="admin-progress-lesson")
router.register("progress/missions", MissionProgressAdminViewSet, basename="admin-progress-mission")
router.register("progress/mission-exam-attempts", MissionExamAttemptAdminViewSet, basename="admin-progress-examattempt")
router.register("progress/enrollments", EnrollmentAdminViewSet, basename="admin-progress-enrollment")
router.register("audit-logs", AdminAuditLogViewSet, basename="admin-auditlog")
router.register("assistant-prompt-notes", AssistantPromptNoteAdminViewSet, basename="admin-assistant-note")

urlpatterns = [
    path("auth/login/", AdminTokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", AdminMeView.as_view()),
    path("analytics/overview/", AnalyticsOverviewView.as_view()),
    path("analytics/content/", AnalyticsContentView.as_view()),
    path("analytics/activity/", AnalyticsActivityView.as_view()),
    path("assistant-prompt/", AssistantPromptSettingsView.as_view()),
    path("", include(router.urls)),
]
