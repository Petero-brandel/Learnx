from rest_framework import serializers
from .models import Course, Module, Lesson, Quiz, Question, Answer


# ─── Quiz Serializers (Admin — includes is_correct) ─────────

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'answers']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'lesson', 'passing_score', 'max_attempts',
            'time_limit_minutes', 'is_required', 'show_correct_answers',
            'shuffle_questions', 'shuffle_answers', 'questions',
        ]


# ─── Quiz Serializers (Student — hides is_correct) ──────────

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text']


class StudentQuestionSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'answers']


class StudentQuizSerializer(serializers.ModelSerializer):
    questions = StudentQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'passing_score', 'max_attempts', 'time_limit_minutes',
            'is_required', 'show_correct_answers', 'shuffle_questions',
            'shuffle_answers', 'questions',
        ]


# ─── Bulk Save Serializer (Admin) ───────────────────────────

class BulkAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    text = serializers.CharField(max_length=500)
    is_correct = serializers.BooleanField(default=False)


class BulkQuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    text = serializers.CharField()
    question_type = serializers.ChoiceField(
        choices=['multiple_choice', 'true_false'],
        default='multiple_choice'
    )
    order = serializers.IntegerField(default=0)
    answers = BulkAnswerSerializer(many=True)


class QuizBulkSaveSerializer(serializers.Serializer):
    passing_score = serializers.IntegerField(default=70, min_value=0, max_value=100)
    max_attempts = serializers.IntegerField(default=0, min_value=0)
    time_limit_minutes = serializers.IntegerField(default=0, min_value=0)
    is_required = serializers.BooleanField(default=True)
    show_correct_answers = serializers.BooleanField(default=True)
    shuffle_questions = serializers.BooleanField(default=False)
    shuffle_answers = serializers.BooleanField(default=False)
    questions = BulkQuestionSerializer(many=True)


# ─── Quiz Submission Serializer (Student) ────────────────────

class QuizSubmissionSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Map of question_id to selected_answer_id'
    )
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    time_taken_seconds = serializers.IntegerField(required=False, default=0, min_value=0)


# ─── Lesson Serializers ─────────────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'content_type', 'video_id',
            'text_content', 'file_url', 'order', 'is_preview', 'quiz',
        ]


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'price', 'thumbnail', 'is_published', 'created_at', 'updated_at', 'modules']


class CourseListSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'price', 'thumbnail', 'is_published', 'created_at', 'modules']


class LessonReorderSerializer(serializers.Serializer):
    lesson_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of lesson IDs in their new order."
    )
