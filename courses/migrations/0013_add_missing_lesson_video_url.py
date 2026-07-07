from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0012_add_missing_cover_color_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE "courses_lesson"
                ADD COLUMN IF NOT EXISTS "video_url" varchar(500) NOT NULL DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
