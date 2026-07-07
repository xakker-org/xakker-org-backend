from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0006_create_missing_tables"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Mission",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(max_length=200)),
                        ("slug", models.SlugField(unique=True)),
                        ("description", models.TextField()),
                        ("short_description", models.CharField(blank=True, max_length=300)),
                        (
                            "difficulty",
                            models.CharField(
                                choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard"), ("expert", "Expert")],
                                default="medium",
                                max_length=20,
                            ),
                        ),
                        ("cover_color", models.CharField(blank=True, default="#4d9fff", max_length=16)),
                        ("icon", models.CharField(blank=True, default="🎯", max_length=8)),
                        ("estimated_hours", models.PositiveSmallIntegerField(default=1)),
                        ("xp_reward", models.PositiveIntegerField(default=100)),
                        ("order", models.PositiveSmallIntegerField(default=0)),
                        ("is_published", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"ordering": ["order", "created_at"]},
                ),
                migrations.CreateModel(
                    name="MissionPass",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(max_length=200)),
                        ("content", models.TextField(help_text="HTML content for this pass. Supports standard HTML tags.")),
                        ("order", models.PositiveSmallIntegerField(default=0)),
                        ("estimated_minutes", models.PositiveSmallIntegerField(default=10)),
                        ("is_published", models.BooleanField(default=True)),
                        ("mission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="passes", to="courses.mission")),
                    ],
                    options={"ordering": ["order"], "verbose_name": "Mission Pass", "verbose_name_plural": "Mission Passes", "unique_together": {("mission", "order")}},
                ),
                migrations.CreateModel(
                    name="MissionExam",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(max_length=200)),
                        ("description", models.TextField(blank=True)),
                        ("passing_score", models.PositiveSmallIntegerField(default=70, help_text="Minimum percentage (0-100) required to pass")),
                        ("time_limit_minutes", models.PositiveSmallIntegerField(default=0, help_text="Time limit in minutes. Set 0 for no limit.")),
                        ("max_attempts", models.PositiveSmallIntegerField(default=3, help_text="Maximum allowed attempts. Set 0 for unlimited.")),
                        ("xp_reward", models.PositiveIntegerField(default=50)),
                        ("is_published", models.BooleanField(default=True)),
                        ("mission", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="mission_exam", to="courses.mission")),
                    ],
                    options={"verbose_name": "Mission Exam"},
                ),
                migrations.CreateModel(
                    name="MissionExamQuestion",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("question_text", models.TextField()),
                        (
                            "question_type",
                            models.CharField(
                                choices=[("closed", "Closed"), ("open", "Open")],
                                default="closed",
                                max_length=20,
                            ),
                        ),
                        ("order", models.PositiveSmallIntegerField(default=0)),
                        ("is_multiple", models.BooleanField(default=False, help_text="Allow multiple correct answers to be selected")),
                        ("expected_answer", models.TextField(blank=True, default="", help_text="Expected answer for open questions.")),
                        ("explanation", models.TextField(blank=True, help_text="Shown after the exam to explain the correct answer")),
                        ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="courses.missionexam")),
                    ],
                    options={"ordering": ["order"], "verbose_name": "Exam Question"},
                ),
                migrations.CreateModel(
                    name="MissionExamChoice",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("choice_text", models.CharField(max_length=500)),
                        ("is_correct", models.BooleanField(default=False)),
                        ("order", models.PositiveSmallIntegerField(default=0)),
                        ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="courses.missionexamquestion")),
                    ],
                    options={"ordering": ["order"], "verbose_name": "Exam Choice"},
                ),
                migrations.CreateModel(
                    name="MissionProgress",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("started_at", models.DateTimeField(auto_now_add=True)),
                        ("completed_at", models.DateTimeField(blank=True, null=True)),
                        ("is_completed", models.BooleanField(default=False)),
                        ("exam_passed", models.BooleanField(default=False)),
                        ("mission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_progress", to="courses.mission")),
                        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mission_progress", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={"verbose_name": "Mission Progress", "verbose_name_plural": "Mission Progress", "unique_together": {("user", "mission")}},
                ),
                migrations.CreateModel(
                    name="MissionPassCompletion",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("completed_at", models.DateTimeField(auto_now_add=True)),
                        ("mission_pass", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="completions", to="courses.missionpass")),
                        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pass_completions", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={"verbose_name": "Pass Completion", "unique_together": {("user", "mission_pass")}},
                ),
                migrations.CreateModel(
                    name="MissionExamAttempt",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("attempt_number", models.PositiveSmallIntegerField(default=1)),
                        ("started_at", models.DateTimeField(auto_now_add=True)),
                        ("submitted_at", models.DateTimeField(blank=True, null=True)),
                        ("score", models.FloatField(blank=True, null=True)),
                        ("passed", models.BooleanField(default=False)),
                        ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="courses.missionexam")),
                        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mission_exam_attempts", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={"ordering": ["-started_at"], "verbose_name": "Exam Attempt", "unique_together": {("user", "exam", "attempt_number")}},
                ),
                migrations.CreateModel(
                    name="MissionExamAnswer",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("submitted_answer", models.TextField(blank=True, default="")),
                        ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="courses.missionexamattempt")),
                        ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="courses.missionexamquestion")),
                        ("selected_choices", models.ManyToManyField(blank=True, to="courses.missionexamchoice")),
                    ],
                    options={"verbose_name": "Exam Answer", "unique_together": {("attempt", "question")}},
                ),
            ],
        ),
    ]
