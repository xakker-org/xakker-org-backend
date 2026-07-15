import hashlib

from django.conf import settings
from django.db import models


class CtfDifficultyChoices(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"
    EXPERT = "expert", "Expert"


class CtfMissionStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class CtfUserMissionStatusChoices(models.TextChoices):
    NOT_STARTED = "not_started", "Not started"
    ATTEMPTED = "attempted", "Attempted"
    SOLVED = "solved", "Solved"


class MissionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Mission category"
        verbose_name_plural = "Mission categories"

    def __str__(self):
        return self.name


class MissionTag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Mission(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    difficulty = models.CharField(
        max_length=20,
        choices=CtfDifficultyChoices.choices,
        default=CtfDifficultyChoices.MEDIUM,
    )
    category = models.ForeignKey(
        MissionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="missions",
    )
    tags = models.ManyToManyField(MissionTag, blank=True, related_name="missions")
    short_description = models.CharField(max_length=300, blank=True, default="")
    description = models.TextField(blank=True, default="")
    connection_info = models.TextField(blank=True, default="")
    points = models.PositiveIntegerField(default=100)
    estimated_time = models.PositiveIntegerField(default=30, help_text="Minutes")
    status = models.CharField(
        max_length=20,
        choices=CtfMissionStatusChoices.choices,
        default=CtfMissionStatusChoices.DRAFT,
    )
    flag_hash = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @staticmethod
    def _normalize(plaintext):
        return (plaintext or "").strip()

    def set_flag(self, plaintext):
        normalized = self._normalize(plaintext)
        self.flag_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def check_flag(self, plaintext):
        if not self.flag_hash:
            return False
        normalized = self._normalize(plaintext)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest() == self.flag_hash

    @property
    def has_flag(self):
        return bool(self.flag_hash)


class Writeup(models.Model):
    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name="writeup")
    content = models.TextField(blank=True, default="")
    is_locked_by_default = models.BooleanField(default=True)

    def __str__(self):
        return f"Writeup · {self.mission.title}"


class UserMissionProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ctf_progress"
    )
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="user_progress")
    status = models.CharField(
        max_length=20,
        choices=CtfUserMissionStatusChoices.choices,
        default=CtfUserMissionStatusChoices.NOT_STARTED,
    )
    flag_attempts = models.PositiveIntegerField(default=0)
    solved_at = models.DateTimeField(null=True, blank=True)
    writeup_unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "mission")
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user.username} · {self.mission.title} · {self.status}"

    @property
    def writeup_unlocked(self):
        writeup = getattr(self.mission, "writeup", None)
        if writeup is None:
            return False
        if self.writeup_unlocked_at is not None:
            return True
        if not writeup.is_locked_by_default:
            return True
        return self.status == CtfUserMissionStatusChoices.SOLVED
