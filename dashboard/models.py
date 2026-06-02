from django.db import models

class BroadcastHistory(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    target_audience = models.CharField(max_length=255) # 'all' or comma-separated course_ids
    recipients_count = models.IntegerField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.subject} ({self.target_audience})"
