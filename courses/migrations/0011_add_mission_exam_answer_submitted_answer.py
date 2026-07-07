from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0010_add_mission_exam_question_expected_answer"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE "courses_missionexamanswer"
                        ADD COLUMN IF NOT EXISTS "submitted_answer" text NOT NULL DEFAULT '';
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
