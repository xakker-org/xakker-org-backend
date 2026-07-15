from django.conf import settings
from django.db import models
from django.utils import timezone


class LevelChoices(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class TaskAnswerKind(models.TextChoices):
    TEXT = "text", "Text match"
    FLAG = "flag", "Flag string"
    CHOICE = "choice", "Multiple choice"
    NUMERIC = "numeric", "Numeric"
    REVIEW = "review", "Manual review"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, default="🛡️")
    color = models.CharField(max_length=16, blank=True, default="#ff5672")
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, default="📘")
    cover_color = models.CharField(max_length=16, blank=True, default="#ff5672")
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class LearningPlan(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=8, blank=True, default="🧭")
    level = models.CharField(max_length=20, choices=LevelChoices.choices, default=LevelChoices.BEGINNER)
    estimated_hours = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    courses = models.ManyToManyField(Course, through="LearningPlanCourse", related_name="learning_plans")

    def __str__(self):
        return self.title


class LearningPlanCourse(models.Model):
    plan = models.ForeignKey(LearningPlan, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("plan", "course")

    def __str__(self):
        return f"{self.plan.title} -> {self.course.title}"


class RoomTag(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="rooms")
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    ENV_CHOICES = [
        ("docker",   "Docker"),
        ("vm",       "Virtual Machine"),
        ("linux",    "Linux"),
        ("windows",  "Windows"),
        ("web",      "Web App"),
        ("cloud",    "Cloud"),
    ]

    icon = models.CharField(max_length=8, blank=True, default="🧪")
    cover_color = models.CharField(max_length=16, blank=True, default="#ff5672")
    level = models.CharField(max_length=20, choices=LevelChoices.choices, default=LevelChoices.BEGINNER)
    env = models.CharField(
        max_length=20, choices=ENV_CHOICES, default="docker", blank=True,
        verbose_name="Lab Environment",
        help_text="Type of isolated environment (Docker, VM, Web App…).",
    )
    target_ip = models.CharField(
        max_length=40, blank=True, default="10.10.11.1",
        verbose_name="Target IP",
        help_text="IP address shown to students in the terminal.",
    )
    estimated_minutes = models.PositiveIntegerField(default=45)
    points = models.PositiveIntegerField(default=100)
    is_premium = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(RoomTag, related_name="rooms", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default="")
    video_url = models.CharField(max_length=500, blank=True, default="", help_text="YouTube URL or direct video URL")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_questions")
    text = models.TextField(help_text="Question text shown to the student")
    explanation = models.TextField(blank=True, default="", help_text="Shown after answering")
    at_seconds = models.IntegerField(
        null=True, blank=True, default=None,
        help_text="Video timestamp (seconds). Leave blank for inline questions.",
    )
    points = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"[Lesson {self.lesson_id}] Q{self.order}: {self.text[:60]}"


class LessonQuestionChoice(models.Model):
    question = models.ForeignKey(LessonQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{'✓' if self.is_correct else '○'} {self.text[:60]}"


class LessonQuestionAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_question_attempts"
    )
    question = models.ForeignKey(LessonQuestion, on_delete=models.CASCADE, related_name="attempts")
    selected_choice = models.ForeignKey(
        LessonQuestionChoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question")
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.user.username} · LessonQ{self.question_id} · {'✓' if self.is_correct else '✗'}"


class UserLessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="user_progress")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user.username} · {self.lesson.title} · {'✓' if self.is_completed else '…'}"


class Task(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120)
    content = models.TextField(help_text="Markdown body")
    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("room", "slug")

    def __str__(self):
        return f"{self.room.title} · {self.title}"


class TaskQuestion(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="questions")
    prompt = models.CharField(max_length=400)
    kind = models.CharField(max_length=16, choices=TaskAnswerKind.choices, default=TaskAnswerKind.TEXT)
    answer = models.CharField(max_length=255, blank=True, default="")
    hint = models.TextField(blank=True, default="")
    hint_cost = models.PositiveIntegerField(default=5)
    explanation = models.TextField(blank=True, default="")
    points = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)
    case_sensitive = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.task.title} · Q{self.order}"

    def check_answer(self, submitted):
        if self.kind == TaskAnswerKind.REVIEW:
            return None
        expected = (self.answer or "").strip()
        provided = (submitted or "").strip()
        if self.kind == TaskAnswerKind.NUMERIC:
            try:
                return float(provided) == float(expected)
            except (TypeError, ValueError):
                return False
        if self.case_sensitive:
            return provided == expected
        return provided.casefold() == expected.casefold()


class TaskQuestionChoice(models.Model):
    question = models.ForeignKey(TaskQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.question.prompt[:40]} → {self.text[:30]}"


class UserTaskProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_progress")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="user_progress")
    completed = models.BooleanField(default=False)
    earned_points = models.PositiveIntegerField(default=0)
    hint_used = models.BooleanField(default=False)
    first_attempt_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "task")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} · {self.task.title} · {'✓' if self.completed else '…'}"


class UserQuestionAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_answers")
    question = models.ForeignKey(TaskQuestion, on_delete=models.CASCADE, related_name="attempts")
    submitted_answer = models.TextField(blank=True, default="")
    is_correct = models.BooleanField(default=False)
    awarded_points = models.PositiveIntegerField(default=0)
    hint_used = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.user.username} · Q{self.question_id} · {self.is_correct}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} -> {self.course.title}"


# ═══════════════════════════════════════════════════════════════
#  MISSION / PASS SYSTEM
# ═══════════════════════════════════════════════════════════════

class MissionDifficultyChoices(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"
    EXPERT = "expert", "Expert"


class Mission(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=MissionDifficultyChoices.choices,
        default=MissionDifficultyChoices.MEDIUM,
    )
    cover_color = models.CharField(max_length=16, blank=True, default="#4d9fff")
    icon = models.CharField(max_length=8, blank=True, default="🎯")
    estimated_hours = models.PositiveSmallIntegerField(default=1)
    xp_reward = models.PositiveIntegerField(default=100)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title

    @property
    def pass_count(self):
        return self.passes.filter(is_published=True).count()

    @property
    def has_exam(self):
        return hasattr(self, "mission_exam") and self.mission_exam.is_published


class MissionPass(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="passes")
    title = models.CharField(max_length=200)
    content = models.TextField(
        help_text="HTML content for this pass. Supports standard HTML tags."
    )
    order = models.PositiveSmallIntegerField(default=0)
    estimated_minutes = models.PositiveSmallIntegerField(default=10)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = [["mission", "order"]]
        verbose_name = "Mission Pass"
        verbose_name_plural = "Mission Passes"

    def __str__(self):
        return f"{self.mission.title} — Pass {self.order}: {self.title}"


class MissionExam(models.Model):
    mission = models.OneToOneField(
        Mission, on_delete=models.CASCADE, related_name="mission_exam"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.PositiveSmallIntegerField(
        default=70, help_text="Minimum percentage (0-100) required to pass"
    )
    time_limit_minutes = models.PositiveSmallIntegerField(
        default=0, help_text="Time limit in minutes. Set 0 for no limit."
    )
    max_attempts = models.PositiveSmallIntegerField(
        default=3, help_text="Maximum allowed attempts. Set 0 for unlimited."
    )
    xp_reward = models.PositiveIntegerField(default=50)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Mission Exam"

    def __str__(self):
        return f"Final Exam: {self.mission.title}"


class MissionExamQuestionTypeChoices(models.TextChoices):
    CLOSED = "closed", "Closed"
    OPEN = "open", "Open"


class MissionExamQuestion(models.Model):
    exam = models.ForeignKey(MissionExam, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=MissionExamQuestionTypeChoices.choices,
        default=MissionExamQuestionTypeChoices.CLOSED,
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_multiple = models.BooleanField(
        default=False, help_text="Allow multiple correct answers to be selected"
    )
    expected_answer = models.TextField(
        blank=True, default="", help_text="Expected answer for open questions."
    )
    explanation = models.TextField(
        blank=True, help_text="Shown after the exam to explain the correct answer"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Exam Question"

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:80]}"


class MissionExamChoice(models.Model):
    question = models.ForeignKey(
        MissionExamQuestion, on_delete=models.CASCADE, related_name="choices"
    )
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Exam Choice"

    def __str__(self):
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.choice_text[:60]}"


class MissionProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mission_progress",
    )
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE, related_name="user_progress"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    exam_passed = models.BooleanField(default=False)

    class Meta:
        unique_together = [["user", "mission"]]
        verbose_name = "Mission Progress"
        verbose_name_plural = "Mission Progress"

    def __str__(self):
        status = "completed" if self.is_completed else "in progress"
        return f"{self.user.username} — {self.mission.title} ({status})"


class MissionPassCompletion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pass_completions",
    )
    mission_pass = models.ForeignKey(
        MissionPass, on_delete=models.CASCADE, related_name="completions"
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "mission_pass"]]
        verbose_name = "Pass Completion"

    def __str__(self):
        return f"{self.user.username} — {self.mission_pass}"


class MissionExamAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mission_exam_attempts",
    )
    exam = models.ForeignKey(MissionExam, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = [["user", "exam", "attempt_number"]]
        ordering = ["-started_at"]
        verbose_name = "Exam Attempt"

    def __str__(self):
        return f"{self.user.username} — {self.exam} — Attempt #{self.attempt_number}"


class MissionExamAnswer(models.Model):
    attempt = models.ForeignKey(
        MissionExamAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(MissionExamQuestion, on_delete=models.CASCADE)
    submitted_answer = models.TextField(blank=True, default="")
    selected_choices = models.ManyToManyField(MissionExamChoice, blank=True)

    class Meta:
        unique_together = [["attempt", "question"]]
        verbose_name = "Exam Answer"

    def __str__(self):
        return f"Answer to {self.question} in {self.attempt}"
