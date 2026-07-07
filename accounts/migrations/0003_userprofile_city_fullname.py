from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_add_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="city",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="full_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
    ]
