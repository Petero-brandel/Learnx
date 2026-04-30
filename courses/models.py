from django.db import models
from django.utils.text import slugify

class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    thumbnail = models.URLField(max_length=1024, blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('text', 'Text/Article'),
        ('pdf', 'PDF Download'),
        ('quiz', 'Quiz'),
    )

    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='video')
    
    # Bunny Stream Integration
    video_id = models.CharField(max_length=255, blank=True, null=True, help_text="Bunny Stream Video GUID")
    
    text_content = models.TextField(blank=True, null=True)
    file_url = models.URLField(max_length=1024, blank=True, null=True)
    
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False, help_text="Can be watched without purchasing")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"
