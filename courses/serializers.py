from rest_framework import serializers
from .models import Course, Module, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Hides sensitive content fields (video_id, text_content, file_url) unless
    the lesson is marked as preview OR the requesting user is enrolled.
    Admin users always see everything.
    """
    video_id = serializers.SerializerMethodField()
    text_content = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content_type', 'video_id', 'text_content', 'file_url', 'order', 'is_preview']

    def _user_has_access(self, lesson):
        """Check if the current user can access this lesson's content."""
        # Preview lessons are always accessible
        if lesson.is_preview:
            return True

        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False

        # Admin always has access
        if request.user.is_staff:
            return True

        # Check enrollment (cached on the serializer context to avoid N+1 queries)
        enrolled_course_ids = self.context.get('enrolled_course_ids')
        if enrolled_course_ids is not None:
            return lesson.module.course_id in enrolled_course_ids

        # Fallback: query the database
        from payments.models import Enrollment
        return Enrollment.objects.filter(
            user=request.user,
            course=lesson.module.course,
            is_active=True
        ).exists()

    def get_video_id(self, obj):
        return obj.video_id if self._user_has_access(obj) else None

    def get_text_content(self, obj):
        return obj.text_content if self._user_has_access(obj) else None

    def get_file_url(self, obj):
        return obj.file_url if self._user_has_access(obj) else None


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
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'price', 'thumbnail', 'is_published']


class LessonReorderSerializer(serializers.Serializer):
    lesson_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of lesson IDs in their new order."
    )

