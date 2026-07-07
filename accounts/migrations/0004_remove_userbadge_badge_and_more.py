from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_userprofile_city_fullname"),
    ]

    operations = [
        # Clear unique_together BEFORE removing fields
        migrations.AlterUniqueTogether(
            name="userbadge",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="userbadge",
            name="badge",
        ),
        migrations.RemoveField(
            model_name="userbadge",
            name="user",
        ),
        # Migrate any badge_earned activity rows so they don't violate future choice validation
        migrations.RunSQL(
            "UPDATE accounts_activity SET kind = 'task_complete' WHERE kind = 'badge_earned'",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.DeleteModel(name="Badge"),
        migrations.DeleteModel(name="UserBadge"),
    ]
