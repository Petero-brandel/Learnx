from django.db.models import Max
from rest_framework import serializers
from .models import (
    Course,
    Module,
    Lesson,
    Quiz,
    Question,
    Answer,
    QuizAttempt
)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)

        instance.text = validated_data.get('text', instance.text)
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.order = validated_data.get('order', instance.order)
        instance.save()

        if answers_data is not None:
            instance.answers.all().delete()

            for answer_data in answers_data:
                Answer.objects.create(question=instance, **answer_data)

        return instance


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'lesson',
            'passing_score',
            'max_attempts',
            'time_limit_minutes',
            'is_required',
            'show_correct_answers',
            'shuffle_questions',
            'shuffle_answers',
            'questions'
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        quiz = Quiz.objects.create(**validated_data)

        for question_data in questions_data:
            answers_data = question_data.pop('answers', [])
            question = Question.objects.create(
                quiz=quiz,
                **question_data
            )

            for answer_data in answers_data:
                Answer.objects.create(
                    question=question,
                    **answer_data
                )

        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if questions_data is not None:
            instance.questions.all().delete()

            for question_data in questions_data:
                answers_data = question_data.pop('answers', [])

                question = Question.objects.create(
                    quiz=instance,
                    **question_data
                )

                for answer_data in answers_data:
                    Answer.objects.create(
                        question=question,
                        **answer_data
                    )

        return instance


class LessonSerializer(serializers.ModelSerializer):
    module = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all()
    )

    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id',
            'module',
            'title',
            'content_type',
            'video_id',
            'text_content',
            'file_url',
            'order',
            'is_preview',
            'quiz'
        ]

    def create(self, validated_data):
        module = validated_data['module']

        max_order = Lesson.objects.filter(
            module=module
        ).aggregate(
            max_order=Max('order')
        )['max_order']

        validated_data['order'] = (max_order or 0) + 1

        return super().create(validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all()
    )

    class Meta:
        model = Module
        fields = [
            'id',
            'course',
            'title',
            'order',
            'lessons'
        ]

    def create(self, validated_data):
        course = validated_data['course']

        max_order = Module.objects.filter(
            course=course
        ).aggregate(
            max_order=Max('order')
        )['max_order']

        validated_data['order'] = (max_order or 0) + 1

        return super().create(validated_data)


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'price',
            'thumbnail',
            'preview_video_id',
            'is_published',
            'created_at',
            'updated_at',
            'modules'
        ]


class CourseListSerializer(serializers.ModelSerializer):
    module_count = serializers.IntegerField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'price',
            'thumbnail',
            'preview_video_id',
            'is_published',
            'created_at',
            'module_count',
            'lesson_count',
        ]


class LessonReorderSerializer(serializers.Serializer):
    lesson_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of lesson IDs in their new order."
    )


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            'id',
            'user',
            'quiz',
            'score',
            'passed',
            'time_taken_seconds',
            'selected_answers',
            'attempted_at'
        ]