import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from .models import Course, Module, Lesson
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, 
    ModuleSerializer, LessonSerializer, LessonReorderSerializer
)
from .bunny import create_video_object

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly] # Admin handles create/update, public can read
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        # Public users only see published courses. Admin sees all.
        queryset = Course.objects.prefetch_related('modules__lessons')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_published=True)

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAdminUser] # Only owner dashboard manages modules

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Receives an array of lesson IDs in the new order.
        Optimized for the mobile touch-handle UI.
        """
        serializer = LessonReorderSerializer(data=request.data)
        if serializer.is_valid():
            lesson_ids = serializer.validated_data['lesson_ids']
            for index, lesson_id in enumerate(lesson_ids):
                Lesson.objects.filter(id=lesson_id).update(order=index)
            return Response({'status': 'reordered'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def request_upload_url(self, request, pk=None):
        """
        Requests a TUS direct-upload GUID from Bunny Stream for a specific lesson.
        """
        lesson = self.get_object()
        if lesson.content_type != 'video':
            return Response({'error': 'Lesson is not a video type.'}, status=status.HTTP_400_BAD_REQUEST)

        # Call Bunny API
        guid = create_video_object(f"Lesson {lesson.id} - {lesson.title}")
        
        if guid:
            # Save the GUID to the lesson so we know which video it belongs to
            lesson.video_id = guid
            lesson.save()
            return Response({
                'video_id': guid,
                'library_id': os.environ.get('BUNNY_LIBRARY_ID')
            })
        
        return Response({'error': 'Failed to communicate with Bunny Stream.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
