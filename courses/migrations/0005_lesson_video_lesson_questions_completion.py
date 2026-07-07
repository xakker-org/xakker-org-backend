import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_question_expected_answer_questionattempt"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- Course: cover_color already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="course",
                    name="cover_color",
                    field=models.CharField(blank=True, default="#ff5672", max_length=16),
                ),
            ],
            database_operations=[],
        ),
        # --- Lesson: video_url already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="lesson",
                    name="video_url",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text="YouTube URL or direct video URL",
                        max_length=500,
                    ),
                ),
                migrations.AlterField(
                    model_name="lesson",
                    name="content",
                    field=models.TextField(blank=True, default=""),
                ),
            ],
            database_operations=[],
        ),
        # --- LessonQuestion: table already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="LessonQuestion",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("text", models.TextField(help_text="Question text shown to the student")),
                        ("explanation", models.TextField(blank=True, default="", help_text="Shown after answering")),
                        (
                            "at_seconds",
                            models.IntegerField(
                                blank=True,
                                default=None,
                                help_text="Video timestamp (seconds). Leave blank for inline questions.",
                                null=True,
                            ),
                        ),
                        ("points", models.PositiveIntegerField(default=10)),
                        ("order", models.PositiveIntegerField(default=1)),
                        (
                            "lesson",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="lesson_questions",
                                to="courses.lesson",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["order", "id"],
                    },
                ),
            ],
            database_operations=[],
        ),
        # --- LessonQuestionChoice: table already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="LessonQuestionChoice",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("text", models.CharField(max_length=400)),
                        ("is_correct", models.BooleanField(default=False)),
                        ("order", models.PositiveIntegerField(default=1)),
                        (
                            "question",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="choices",
                                to="courses.lessonquestion",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["order", "id"],
                    },
                ),
            ],
            database_operations=[],
        ),
        # --- LessonQuestionAttempt: table already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="LessonQuestionAttempt",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("is_correct", models.BooleanField(default=False)),
                        ("points_awarded", models.PositiveIntegerField(default=0)),
                        ("attempted_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "question",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="attempts",
                                to="courses.lessonquestion",
                            ),
                        ),
                        (
                            "selected_choice",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="+",
                                to="courses.lessonquestionchoice",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="lesson_question_attempts",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["-attempted_at"],
                        "unique_together": {("user", "question")},
                    },
                ),
            ],
            database_operations=[],
        ),
        # --- UserLessonProgress: table already exists in DB, only update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="UserLessonProgress",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("is_completed", models.BooleanField(default=False)),
                        ("completed_at", models.DateTimeField(null=True, blank=True)),
                        (
                            "lesson",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="user_progress",
                                to="courses.lesson",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="lesson_progress",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "unique_together": {("user", "lesson")},
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
