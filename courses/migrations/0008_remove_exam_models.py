from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_mission_state_sync"),
    ]

    operations = [
        # Clear unique_together constraints FIRST, before removing fields
        migrations.AlterUniqueTogether(
            name="examattemptanswer",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="examquestion",
            unique_together=set(),
        ),
        # Remove FK fields from ExamQuestion
        migrations.RemoveField(model_name="examquestion", name="exam"),
        migrations.RemoveField(model_name="examquestion", name="question"),
        # Remove FK fields from ExamAttempt
        migrations.RemoveField(model_name="examattempt", name="exam"),
        migrations.RemoveField(model_name="examattempt", name="user"),
        # Remove FK fields from ExamAttemptAnswer
        migrations.RemoveField(model_name="examattemptanswer", name="attempt"),
        migrations.RemoveField(model_name="examattemptanswer", name="question"),
        migrations.RemoveField(model_name="examattemptanswer", name="selected_choice"),
        # Delete models
        migrations.DeleteModel(name="Exam"),
        migrations.DeleteModel(name="ExamAttempt"),
        migrations.DeleteModel(name="ExamAttemptAnswer"),
        migrations.DeleteModel(name="ExamQuestion"),
    ]
