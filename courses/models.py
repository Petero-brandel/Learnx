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


class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, related_name='quiz', on_delete=models.CASCADE)
    passing_score = models.PositiveIntegerField(default=70, help_text="Minimum % to pass")
    max_attempts = models.PositiveIntegerField(default=0, help_text="0 = unlimited attempts")
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text="0 = no time limit")
    is_required = models.BooleanField(default=True, help_text="Must pass to mark lesson complete")
    show_correct_answers = models.BooleanField(default=True, help_text="Reveal correct answers after submission")
    shuffle_questions = models.BooleanField(default=False, help_text="Randomize question order per attempt")
    shuffle_answers = models.BooleanField(default=False, help_text="Randomize answer order per attempt")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz for: {self.lesson.title}"


class Question(models.Model):
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True / False'),
    )

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:50]}"
