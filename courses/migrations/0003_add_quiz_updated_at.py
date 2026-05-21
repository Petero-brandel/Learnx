from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_question_answer_quiz_question_quiz_quizattempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]