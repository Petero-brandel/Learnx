from rest_framework import serializers
from .models import Course, Module, Lesson

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content_type', 'video_id', 'text_content', 'file_url', 'order', 'is_preview']

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']

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
