from rest_framework import serializers
from .models import Course, Module, Lesson

class LessonSerializer(serializers.ModelSerializer):
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())

    class Meta:
        model = Lesson
        fields = ['id', 'module', 'title', 'content_type', 'video_id', 'text_content', 'file_url', 'order', 'is_preview']

    def create(self, validated_data):
        # Auto-assign order so new lessons always appear at the bottom
        module = validated_data['module']
        max_order = Lesson.objects.filter(module=module).aggregate(
            max_order=serializers.models.Max('order')
        )['max_order']
        validated_data['order'] = (max_order or 0) + 1
        return super().create(validated_data)

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']

    def create(self, validated_data):
        course = validated_data['course']
        max_order = Module.objects.filter(course=course).aggregate(
            max_order=serializers.models.Max('order')
        )['max_order']
        validated_data['order'] = (max_order or 0) + 1
        return super().create(validated_data)

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
