from django.urls import path

from .views import (
    CabinetView,
    CategoryListView,
    CourseDetailView,
    CourseListView,
    EnrollmentCreateView,
    LearningPlanDetailView,
    LearningPlanListView,
    LessonCompleteView,
    LessonDetailView,
    LessonQuestionSubmitView,
    MissionDetailView,
    MissionExamDetailView,
    MissionExamStartView,
    MissionExamSubmitView,
    MissionListView,
    MissionPassCompleteView,
    MissionPassDetailView,
    MissionStartView,
    MyMissionProgressView,
    RoomDetailView,
    RoomEnrollView,
    RoomListView,
    RoomTagListView,
    TaskAnswerSubmitView,
    TaskDetailView,
    TaskHintView,
)

urlpatterns = [
    path("", CourseListView.as_view(), name="course-list"),
    path("cabinet/", CabinetView.as_view(), name="cabinet"),

    # Plans
    path("plans/", LearningPlanListView.as_view(), name="learning-plan-list"),
    path("plans/<slug:slug>/", LearningPlanDetailView.as_view(), name="learning-plan-detail"),

    # Rooms / tasks
    path("rooms/", RoomListView.as_view(), name="room-list"),
    path("rooms/tags/", RoomTagListView.as_view(), name="room-tags"),
    path("rooms/<slug:slug>/", RoomDetailView.as_view(), name="room-detail"),
    path("rooms/<slug:slug>/enroll/", RoomEnrollView.as_view(), name="room-enroll"),
    path("rooms/<slug:room_slug>/tasks/<slug:task_slug>/", TaskDetailView.as_view(), name="task-detail"),
    path("rooms/<slug:room_slug>/tasks/<slug:task_slug>/answer/", TaskAnswerSubmitView.as_view(), name="task-answer"),
    path(
        "rooms/<slug:room_slug>/tasks/<slug:task_slug>/hint/<int:question_id>/",
        TaskHintView.as_view(),
        name="task-hint",
    ),

    # Categories
    path("categories/", CategoryListView.as_view(), name="category-list"),

    # Enrollment
    path("enroll/", EnrollmentCreateView.as_view(), name="course-enroll"),

    # Course lessons
    path("<slug:slug>/lessons/<int:lesson_id>/", LessonDetailView.as_view(), name="lesson-detail"),
    path("<slug:slug>/lessons/<int:lesson_id>/complete/", LessonCompleteView.as_view(), name="lesson-complete"),
    path(
        "<slug:slug>/lessons/<int:lesson_id>/questions/<int:question_id>/submit/",
        LessonQuestionSubmitView.as_view(),
        name="lesson-question-submit",
    ),

    # ── Missions ──────────────────────────────────────────────
    path("missions/", MissionListView.as_view(), name="mission-list"),
    path("missions/my-progress/", MyMissionProgressView.as_view(), name="mission-my-progress"),
    path("missions/<slug:slug>/", MissionDetailView.as_view(), name="mission-detail"),
    path("missions/<slug:slug>/start/", MissionStartView.as_view(), name="mission-start"),
    path("missions/<slug:slug>/passes/<int:pass_id>/", MissionPassDetailView.as_view(), name="mission-pass-detail"),
    path("missions/<slug:slug>/passes/<int:pass_id>/complete/", MissionPassCompleteView.as_view(), name="mission-pass-complete"),
    path("missions/<slug:slug>/exam/", MissionExamDetailView.as_view(), name="mission-exam-detail"),
    path("missions/<slug:slug>/exam/start/", MissionExamStartView.as_view(), name="mission-exam-start"),
    path("missions/<slug:slug>/exam/<int:attempt_id>/submit/", MissionExamSubmitView.as_view(), name="mission-exam-submit"),

    # Course detail (keep last so "plans" etc. not shadowed)
    path("<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
]
