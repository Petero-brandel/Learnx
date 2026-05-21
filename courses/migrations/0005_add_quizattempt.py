from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_alter_quiz_updated_at'),   # ← Make sure this matches your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5, default=0)),
                ('passed', models.BooleanField(default=False)),
                ('time_taken_seconds', models.PositiveIntegerField(default=0)),
                ('selected_answers', models.JSONField(default=dict)),
                ('attempted_at', models.DateTimeField(auto_now_add=True)),
                ('quiz', models.ForeignKey(on_delete=models.CASCADE, related_name='attempts', to='courses.quiz')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quiz Attempt',
                'verbose_name_plural': 'Quiz Attempts',
            },
        ),
    ]