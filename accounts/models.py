from django.conf import settings
from django.db import models
from django.utils import timezone


class RankChoices(models.TextChoices):
    RECRUIT = "recruit", "Recruit"
    SCRIPT_KIDDIE = "script_kiddie", "Script Kiddie"
    OPERATIVE = "operative", "Operative"
    HUNTER = "hunter", "Hunter"
    SPECIALIST = "specialist", "Specialist"
    ANALYST = "analyst", "Analyst"
    ARCHITECT = "architect", "Architect"
    OPERATOR = "operator", "Operator"
    GHOST = "ghost", "Ghost"


RANK_THRESHOLDS = [
    (0, RankChoices.RECRUIT),
    (150, RankChoices.SCRIPT_KIDDIE),
    (500, RankChoices.OPERATIVE),
    (1200, RankChoices.HUNTER),
    (2500, RankChoices.SPECIALIST),
    (5000, RankChoices.ANALYST),
    (9000, RankChoices.ARCHITECT),
    (14000, RankChoices.OPERATOR),
    (20000, RankChoices.GHOST),
]


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    xp = models.PositiveIntegerField(default=0)
    rank = models.CharField(
        max_length=32,
        choices=RankChoices.choices,
        default=RankChoices.RECRUIT,
    )
    streak_days = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(blank=True, default="")
    country = models.CharField(max_length=80, blank=True, default="")
    city = models.CharField(max_length=80, blank=True, default="")
    full_name = models.CharField(max_length=150, blank=True, default="")
    avatar_hue = models.PositiveIntegerField(default=210)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    rooms_completed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-xp", "user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.rank})"

    def recompute_rank(self):
        current = RankChoices.RECRUIT
        for threshold, rank in RANK_THRESHOLDS:
            if self.xp >= threshold:
                current = rank
        self.rank = current

    def award_xp(self, amount):
        if amount <= 0:
            return
        self.xp = self.xp + amount
        self.recompute_rank()
        self.last_activity = timezone.now()
        self.save(update_fields=["xp", "rank", "last_activity"])


class Activity(models.Model):
    class Kind(models.TextChoices):
        TASK_COMPLETE = "task_complete", "Task completed"
        ROOM_COMPLETE = "room_complete", "Room completed"
        EXAM_SUBMIT = "exam_submit", "Exam submitted"
        ENROLL = "enroll", "Enrolled"
        RANK_UP = "rank_up", "Rank up"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_log",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=200)
    detail = models.CharField(max_length=255, blank=True, default="")
    xp_delta = models.IntegerField(default=0)
    target_slug = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user.username} · {self.kind}"
