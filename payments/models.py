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

    class Meta:
        unique_together = ('user', 'course') # A user can only enroll in a course once

    def __str__(self):
        return f"{self.user.email} -> {self.course.title}"
