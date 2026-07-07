from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0009_add_mission_exam_question_type"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE "courses_missionexamquestion"
                        ADD COLUMN IF NOT EXISTS "expected_answer" text NOT NULL DEFAULT '';
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
