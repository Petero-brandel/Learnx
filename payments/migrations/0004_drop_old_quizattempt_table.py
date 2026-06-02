from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_enrollment_is_active'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS payments_quizattempt CASCADE;",
            reverse_sql=migrations.RunSQL.noop
        )
    ]
