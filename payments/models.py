from django.db import models
from django.conf import settings
from courses.models import Course

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='payments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='payments', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Amount in Naira
    reference = models.CharField(max_length=100, unique=True, help_text="Unique transaction reference for Paystack")
    paystack_id = models.CharField(max_length=100, blank=True, null=True, help_text="Paystack transaction ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.course.title if self.course else 'Unknown Course'} - {self.status}"

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress_percentage = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="Can the user currently access this course?")

    class Meta:
        unique_together = ('user', 'course') # A user can only enroll in a course once

    def __str__(self):
        return f"{self.user.email} -> {self.course.title}"

class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='lesson_progress', on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', related_name='progress', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} - {'Done' if self.is_completed else 'Pending'}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='quiz_attempts', on_delete=models.CASCADE)
    quiz = models.ForeignKey('courses.Quiz', related_name='attempts', on_delete=models.CASCADE)
    score = models.PositiveIntegerField(help_text="Score as percentage 0-100")
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, help_text='{"question_id": selected_answer_id}')
    started_at = models.DateTimeField(null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.email} - Quiz {self.quiz.id} - {self.score}% {'✓' if self.passed else '✗'}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Enrollment)
def create_enrollment_notification(sender, instance, created, **kwargs):
    if created:
        from notifications.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # 1. Notify student
        Notification.objects.create(
            user=instance.user,
            title="Course Unlocked! 🚀",
            message=f"You now have full access to {instance.course.title}. Happy learning!",
            notification_type='enrollment'
        )
        
        # Dispatch HTML Email
        from django_q.tasks import async_task
        async_task('emails.tasks.send_purchase_email_task', instance.user.id, instance.course.id)
        
        # 2. Notify admin
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New Sale! 💰",
                message=f"{instance.user.email} just enrolled in {instance.course.title}.",
                notification_type='sale'
            )
