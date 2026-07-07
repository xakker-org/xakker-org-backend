from collections import OrderedDict

from django.contrib.admin import AdminSite


MODEL_GROUPS = [
    (
        "Courses",
        {
            "Category",
            "Course",
            "Enrollment",
        },
    ),
    (
        "Lessons",
        {
            "Lesson",
            "LessonQuestion",
            "LessonQuestionAttempt",
            "UserLessonProgress",
        },
    ),
    (
        "Rooms",
        {
            "RoomTag",
            "Room",
            "Task",
            "TaskQuestion",
            "UserTaskProgress",
            "UserQuestionAttempt",
        },
    ),
    (
        "Self-Study Questions",
        {
            "Question",
            "QuestionChoice",
            "QuestionAttempt",
        },
    ),
    (
        "Learning Plans",
        {
            "LearningPlan",
            "LearningPlanCourse",
        },
    ),
    (
        "Missions",
        {
            "Mission",
            "MissionPass",
            "MissionPassCompletion",
            "MissionProgress",
            "MissionExam",
            "MissionExamQuestion",
            "MissionExamChoice",
            "MissionExamAttempt",
            "MissionExamAnswer",
        },
    ),
    (
        "Users / Gamification",
        {
            "UserProfile",
            "Activity",
        },
    ),
]


class GroupedAdminSite(AdminSite):
    site_header = "Xəkər Admin"
    site_title = "Xəkər Admin"
    index_title = "İdarəçilik Paneli"

    def _get_grouped_app_list(self, request):
        app_list = super().get_app_list(request)
        model_lookup = {}

        for app in app_list:
            for model in app.get("models", []):
                model_lookup[model["object_name"]] = model

        grouped = []
        used = set()

        for group_name, object_names in MODEL_GROUPS:
            models = [model_lookup[name] for name in object_names if name in model_lookup]
            if not models:
                continue

            used.update(model["object_name"] for model in models)
            grouped.append(
                {
                    "name": group_name,
                    "app_label": group_name.lower().replace(" ", "_").replace("/", "_"),
                    "app_url": None,
                    "has_module_perms": True,
                    "models": models,
                }
            )

        remaining = OrderedDict()
        for app in app_list:
            models = [model for model in app.get("models", []) if model["object_name"] not in used]
            if models:
                remaining[app["name"]] = {
                    "name": app["name"],
                    "app_label": app["app_label"],
                    "app_url": app.get("app_url"),
                    "has_module_perms": app.get("has_module_perms", True),
                    "models": models,
                }

        return grouped + list(remaining.values())

    def get_app_list(self, request):
        return self._get_grouped_app_list(request)

    def each_context(self, request):
        context = super().each_context(request)
        context["available_apps"] = self._get_grouped_app_list(request)
        context["app_list"] = context["available_apps"]
        return context