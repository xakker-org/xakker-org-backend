from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0011_add_mission_exam_answer_submitted_answer"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE "courses_course"
                ADD COLUMN IF NOT EXISTS "cover_color" varchar(16) NOT NULL DEFAULT '#ff5672';
            ALTER TABLE "courses_room"
                ADD COLUMN IF NOT EXISTS "cover_color" varchar(16) NOT NULL DEFAULT '#ff5672';
            ALTER TABLE "courses_lesson"
                ADD COLUMN IF NOT EXISTS "video_url" varchar(500) NOT NULL DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
