from django.contrib import admin
from .models import Course, Module, Lesson, Quiz, Question, Answer

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'is_preview', 'order')
    list_filter = ('content_type', 'is_preview', 'module__course')
    search_fields = ('title',)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'passing_score', 'max_attempts', 'time_limit_minutes', 'is_required')
    list_filter = ('is_required', 'show_correct_answers')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'order')
    list_filter = ('question_type', 'quiz')
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
