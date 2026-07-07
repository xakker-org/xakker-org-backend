from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0013_add_missing_lesson_video_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="env",
            field=models.CharField(
                max_length=20,
                blank=True,
                default="docker",
                choices=[
                    ("docker", "Docker"),
                    ("vm", "Virtual Machine"),
                    ("linux", "Linux"),
                    ("windows", "Windows"),
                    ("web", "Web App"),
                    ("cloud", "Cloud"),
                ],
                verbose_name="Lab Environment",
                help_text="Type of isolated environment for this lab.",
            ),
        ),
        migrations.AddField(
            model_name="room",
            name="target_ip",
            field=models.CharField(
                max_length=40,
                blank=True,
                default="10.10.11.1",
                verbose_name="Target IP",
                help_text="IP address shown to students in the terminal.",
            ),
        ),
    ]
