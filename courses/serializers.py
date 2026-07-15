from rest_framework import serializers

from .models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    LearningPlanCourse,
    Lesson,
    LessonQuestion,
    LessonQuestionAttempt,
    LessonQuestionChoice,
    Mission,
    MissionExam,
    MissionExamAnswer,
    MissionExamAttempt,
    MissionExamChoice,
    MissionExamQuestion,
    MissionPass,
    MissionPassCompletion,
    MissionProgress,
    Room,
    RoomTag,
    Task,
    TaskQuestion,
    TaskQuestionChoice,
    UserLessonProgress,
    UserQuestionAttempt,
    UserTaskProgress,
)


# ----- Shared primitives -----

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "color", "description"]


class RoomTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTag
        fields = ["id", "name", "slug"]


# ----- Courses / plans / lessons -----

class LessonQuestionChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuestionChoice
        fields = ["id", "text", "order"]


class LessonQuestionChoiceFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuestionChoice
        fields = ["id", "text", "order", "is_correct"]


class LessonQuestionSerializer(serializers.ModelSerializer):
    choices = LessonQuestionChoicePublicSerializer(many=True, read_only=True)
    user_attempt = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuestion
        fields = ["id", "text", "explanation", "at_seconds", "points", "order", "choices", "user_attempt"]

    def get_user_attempt(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        attempt = LessonQuestionAttempt.objects.filter(user=request.user, question=obj).first()
        if not attempt:
            return None
        correct_ids = list(obj.choices.filter(is_correct=True).values_list("id", flat=True))
        return {
            "selected_choice_id": attempt.selected_choice_id,
            "is_correct": attempt.is_correct,
            "points_awarded": attempt.points_awarded,
            "attempted_at": attempt.attempted_at,
            "correct_choice_ids": correct_ids,
        }


class LessonSerializer(serializers.ModelSerializer):
    lesson_questions = serializers.SerializerMethodField()
    user_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "content", "video_url", "order", "lesson_questions", "user_completed"]

    def get_lesson_questions(self, obj):
        qs = obj.lesson_questions.prefetch_related("choices").order_by("order", "id")
        return LessonQuestionSerializer(qs, many=True, context=self.context).data

    def get_user_completed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserLessonProgress.objects.filter(
            user=request.user, lesson=obj, is_completed=True
        ).exists()


class CourseSummarySerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "category", "icon", "cover_color"]


class LearningPlanCourseSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(read_only=True)

    class Meta:
        model = LearningPlanCourse
        fields = ["id", "order", "course"]


class LearningPlanSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    room_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningPlan
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "icon",
            "level",
            "estimated_hours",
            "is_featured",
            "courses",
            "room_count",
        ]

    def get_courses(self, obj):
        items = obj.learningplancourse_set.select_related("course", "course__category").order_by("order", "id")
        return LearningPlanCourseSerializer(items, many=True).data

    def get_room_count(self, obj):
        return Room.objects.filter(course__learning_plans=obj, is_published=True).distinct().count()


# ----- Rooms / tasks -----

class TaskQuestionChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskQuestionChoice
        fields = ["id", "text", "order"]


class TaskQuestionPublicSerializer(serializers.ModelSerializer):
    choices = TaskQuestionChoicePublicSerializer(many=True, read_only=True)
    has_hint = serializers.SerializerMethodField()
    user_state = serializers.SerializerMethodField()

    class Meta:
        model = TaskQuestion
        fields = [
            "id",
            "prompt",
            "kind",
            "points",
            "order",
            "hint_cost",
            "has_hint",
            "choices",
            "user_state",
        ]

    def get_has_hint(self, obj):
        return bool(obj.hint)

    def get_user_state(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return None
        last = (
            UserQuestionAttempt.objects.filter(user=user, question=obj)
            .order_by("-attempted_at")
            .first()
        )
        if not last:
            return None
        return {
            "is_correct": last.is_correct,
            "submitted_answer": last.submitted_answer,
            "awarded_points": last.awarded_points,
            "hint_used": last.hint_used,
            "attempted_at": last.attempted_at,
        }


class TaskListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    questions = TaskQuestionPublicSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", "title", "slug", "order", "points", "question_count", "questions", "completed"]

    def get_completed(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        progress = next((p for p in getattr(obj, "_progress_prefetch", []) if p.user_id == user.id), None)
        if progress:
            return progress.completed
        return UserTaskProgress.objects.filter(user=user, task=obj, completed=True).exists()


class TaskDetailSerializer(serializers.ModelSerializer):
    questions = TaskQuestionPublicSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", "title", "slug", "content", "order", "points", "questions", "completed"]

    def get_completed(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        return UserTaskProgress.objects.filter(user=user, task=obj, completed=True).exists()


class RoomListSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(read_only=True)
    tags = RoomTagSerializer(many=True, read_only=True)
    tasks_count = serializers.IntegerField(source="tasks.count", read_only=True)
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "icon",
            "cover_color",
            "level",
            "env",
            "target_ip",
            "estimated_minutes",
            "points",
            "is_premium",
            "course",
            "tags",
            "tasks_count",
            "progress_percent",
        ]

    def get_progress_percent(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return 0
        total = obj.tasks.count()
        if not total:
            return 0
        done = UserTaskProgress.objects.filter(user=user, task__room=obj, completed=True).count()
        return round((done / total) * 100)


class RoomDetailSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(read_only=True)
    tags = RoomTagSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    earned_points = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "icon",
            "cover_color",
            "level",
            "env",
            "target_ip",
            "estimated_minutes",
            "points",
            "is_premium",
            "course",
            "tags",
            "tasks",
            "progress_percent",
            "completed_tasks",
            "total_points",
            "earned_points",
        ]

    def get_tasks(self, obj):
        tasks = obj.tasks.prefetch_related("questions", "questions__choices").all()
        return TaskListSerializer(tasks, many=True, context=self.context).data

    def _user_progress_qs(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return UserTaskProgress.objects.none()
        return UserTaskProgress.objects.filter(user=user, task__room=obj)

    def get_progress_percent(self, obj):
        total = obj.tasks.count()
        if not total:
            return 0
        done = self._user_progress_qs(obj).filter(completed=True).count()
        return round((done / total) * 100)

    def get_completed_tasks(self, obj):
        return self._user_progress_qs(obj).filter(completed=True).count()

    def get_total_points(self, obj):
        return sum(task.points for task in obj.tasks.all()) + sum(
            q.points for task in obj.tasks.all() for q in task.questions.all()
        )

    def get_earned_points(self, obj):
        return sum(p.earned_points for p in self._user_progress_qs(obj))


# ----- Task answer submission -----

class TaskAnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.CharField(allow_blank=True, required=False, default="")
    selected_choice = serializers.IntegerField(required=False, allow_null=True)
    use_hint = serializers.BooleanField(required=False, default=False)


class TaskAnswerResultSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField(allow_null=True)
    awarded_points = serializers.IntegerField()
    xp_delta = serializers.IntegerField()
    explanation = serializers.CharField(allow_blank=True)
    hint = serializers.CharField(allow_blank=True, required=False)
    task_completed = serializers.BooleanField()
    room_completed = serializers.BooleanField()
    badges_earned = serializers.ListField(child=serializers.DictField(), required=False)
    new_rank = serializers.CharField(allow_null=True, required=False)


class LessonQuestionSubmitSerializer(serializers.Serializer):
    selected_choice_id = serializers.IntegerField()


# ----- Cabinet / course list / enrollment -----

class CabinetSummarySerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    account_type = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    enrolled_courses = CourseSummarySerializer(many=True)
    plans = LearningPlanSerializer(many=True)
    rooms = RoomListSerializer(many=True)
    recommended_rooms = RoomListSerializer(many=True)
    profile = serializers.DictField()
    recent_activity = serializers.ListField(child=serializers.DictField())
    stats = serializers.DictField()


class CourseListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    room_count = serializers.IntegerField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "category", "icon", "cover_color", "room_count", "lesson_count"]


class LessonSummarySerializer(serializers.ModelSerializer):
    has_video = serializers.SerializerMethodField()
    has_text = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    user_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "order", "has_video", "has_text", "question_count", "user_completed"]

    def get_has_video(self, obj):
        return bool(obj.video_url)

    def get_has_text(self, obj):
        return bool(obj.content)

    def get_question_count(self, obj):
        return obj.lesson_questions.count()

    def get_user_completed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserLessonProgress.objects.filter(
            user=request.user, lesson=obj, is_completed=True
        ).exists()


class CourseDetailSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()
    learning_plans = LearningPlanSerializer(many=True, read_only=True)
    rooms = serializers.SerializerMethodField()
    lesson_count = serializers.IntegerField(source="lessons.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "category", "icon", "cover_color",
            "lessons", "lesson_count", "learning_plans", "rooms",
        ]

    def get_lessons(self, obj):
        qs = obj.lessons.prefetch_related("lesson_questions").order_by("order")
        return LessonSummarySerializer(qs, many=True, context=self.context).data

    def get_rooms(self, obj):
        rooms = obj.rooms.filter(is_published=True).prefetch_related("tags").order_by("order", "id")
        return RoomListSerializer(rooms, many=True, context=self.context).data


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "user", "course", "created_at"]
        read_only_fields = ["user", "created_at"]


# ═══════════════════════════════════════════════════════════════
#  MISSION SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class MissionExamChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionExamChoice
        fields = ["id", "choice_text", "order"]


class MissionExamChoiceFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionExamChoice
        fields = ["id", "choice_text", "is_correct", "order"]


def _normalize_exam_text(value):
    return " ".join((value or "").split()).casefold()


class MissionExamQuestionSerializer(serializers.ModelSerializer):
    choices = MissionExamChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = MissionExamQuestion
        fields = ["id", "question_text", "question_type", "order", "is_multiple", "choices"]


class MissionExamSerializer(serializers.ModelSerializer):
    questions = MissionExamQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = MissionExam
        fields = [
            "id", "title", "description", "passing_score",
            "time_limit_minutes", "max_attempts", "xp_reward", "questions",
        ]


class MissionExamSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionExam
        fields = ["id", "title", "passing_score", "time_limit_minutes", "max_attempts", "xp_reward"]


class MissionPassListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionPass
        fields = ["id", "title", "order", "estimated_minutes"]


class MissionPassDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionPass
        fields = ["id", "title", "content", "order", "estimated_minutes"]


class MissionListSerializer(serializers.ModelSerializer):
    pass_count = serializers.SerializerMethodField()
    has_exam = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id", "title", "slug", "description", "short_description",
            "difficulty", "cover_color", "icon", "estimated_hours",
            "xp_reward", "order", "pass_count", "has_exam", "user_progress",
        ]

    def get_pass_count(self, obj):
        # `.filter()` builds a fresh QuerySet and always hits the DB, even
        # though the view prefetches `passes` — filter the cached list instead.
        return sum(1 for p in obj.passes.all() if p.is_published)

    def get_has_exam(self, obj):
        return hasattr(obj, "mission_exam") and obj.mission_exam.is_published

    def get_user_progress(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        try:
            prog = obj.user_progress.get(user=request.user)
        except MissionProgress.DoesNotExist:
            return None
        published_passes = [p for p in obj.passes.all() if p.is_published]
        completed = MissionPassCompletion.objects.filter(
            user=request.user, mission_pass__in=published_passes
        ).count()
        return {
            "is_started": True,
            "is_completed": prog.is_completed,
            "exam_passed": prog.exam_passed,
            "completed_passes": completed,
            "total_passes": len(published_passes),
        }


class MissionDetailSerializer(serializers.ModelSerializer):
    passes = serializers.SerializerMethodField()
    exam = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id", "title", "slug", "description", "short_description",
            "difficulty", "cover_color", "icon", "estimated_hours",
            "xp_reward", "order", "passes", "exam", "user_progress",
        ]

    def get_passes(self, obj):
        qs = obj.passes.filter(is_published=True).order_by("order")
        return MissionPassListSerializer(qs, many=True).data

    def get_exam(self, obj):
        if not (hasattr(obj, "mission_exam") and obj.mission_exam.is_published):
            return None
        return MissionExamSummarySerializer(obj.mission_exam).data

    def get_user_progress(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        try:
            prog = obj.user_progress.get(user=request.user)
        except MissionProgress.DoesNotExist:
            return None
        passes = obj.passes.filter(is_published=True)
        completed_ids = list(
            MissionPassCompletion.objects.filter(
                user=request.user, mission_pass__in=passes
            ).values_list("mission_pass_id", flat=True)
        )
        return {
            "is_started": True,
            "is_completed": prog.is_completed,
            "exam_passed": prog.exam_passed,
            "completed_pass_ids": completed_ids,
            "total_passes": passes.count(),
        }


class MissionExamSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(),
        help_text='[{"question_id": 1, "choice_ids": [3, 4]}, ...]',
    )


class MissionExamAttemptResultSerializer(serializers.ModelSerializer):
    answers_detail = serializers.SerializerMethodField()

    class Meta:
        model = MissionExamAttempt
        fields = [
            "id", "attempt_number", "started_at", "submitted_at",
            "score", "passed", "answers_detail",
        ]

    def get_answers_detail(self, obj):
        result = []
        for ans in obj.answers.prefetch_related("selected_choices", "question__choices"):
            q = ans.question
            if q.question_type == "open":
                expected_answers = [
                    part.strip()
                    for part in q.expected_answer.replace("|", "\n").splitlines()
                    if part.strip()
                ]
                selected = (ans.submitted_answer or "").strip()
                result.append({
                    "question_id": q.id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "explanation": q.explanation,
                    "submitted_answer": ans.submitted_answer or "",
                    "expected_answers": expected_answers,
                    "is_correct": _normalize_exam_text(selected) in {_normalize_exam_text(x) for x in expected_answers} if expected_answers else False,
                    "choices": [],
                })
                continue

            selected_ids = set(ans.selected_choices.values_list("id", flat=True))
            correct_ids = set(q.choices.filter(is_correct=True).values_list("id", flat=True))
            result.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "explanation": q.explanation,
                "selected_choice_ids": list(selected_ids),
                "correct_choice_ids": list(correct_ids),
                "is_correct": selected_ids == correct_ids,
                "choices": MissionExamChoiceFullSerializer(q.choices.all(), many=True).data,
            })
        return result
