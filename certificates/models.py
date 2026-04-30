import uuid
from django.db import models
from django.conf import settings
from courses.models import Course

class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='certificates', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='certificates', on_delete=models.CASCADE)
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"Certificate for {self.user.email} - {self.course.title}"
