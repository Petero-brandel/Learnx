import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Course, Module, Lesson, Quiz, Question, Answer, QuizAttempt
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, 
    ModuleSerializer, LessonSerializer, LessonReorderSerializer,
    QuizSerializer, QuestionSerializer, AnswerSerializer, QuizAttemptSerializer
)
from django.utils import timezone
import json
from .bunny import create_video_object

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly] # Admin handles create/update, public can read
    lookup_field = 'slug'

    @method_decorator(cache_page(300))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    def get_serializer_class(self): 
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        queryset = Course.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        if self.action == 'list':
            # Annotate counts instead of nesting full objects — single SQL query
            queryset = queryset.annotate(
                module_count=Count('modules', distinct=True),
                lesson_count=Count('modules__lessons', distinct=True),
            )
        else:
            # Detail view: prefetch the full tree efficiently
            queryset = queryset.prefetch_related(
                'modules__lessons__quiz__questions__answers'
            )

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def request_course_upload_url(self, request, slug=None):
        """
        Requests a TUS direct-upload GUID from Bunny Stream for a course preview.
        """
        course = self.get_object()

        # Call Bunny API
        guid = create_video_object(f"Course Preview - {course.title}")
        
        if guid:
            import time, hashlib
            # Save the GUID to the course so we know which video it belongs to
            course.preview_video_id = guid
            course.save()
            
            library_id = os.environ.get('BUNNY_LIBRARY_ID')
            api_key = os.environ.get('BUNNY_API_KEY')
            expiration_time = int(time.time()) + 3600
            
            # Generate SHA256 signature for Bunny Stream TUS upload
            data_to_hash = f"{library_id}{api_key}{expiration_time}{guid}"
            signature = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
            
            return Response({
                'video_id': guid,
                'library_id': library_id,
                'authorization_signature': signature,
                'authorization_expire': expiration_time
            })
        
        return Response({'error': 'Failed to communicate with Bunny Stream.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def request_new_course_upload_url(self, request):
        """
        Requests a TUS direct-upload GUID from Bunny Stream for a new course preview.
        """
        title = request.data.get('title', 'New Course Preview')
        guid = create_video_object(f"Course Preview - {title}")
        
        if guid:
            import time, hashlib
            library_id = os.environ.get('BUNNY_LIBRARY_ID')
            api_key = os.environ.get('BUNNY_API_KEY')
            expiration_time = int(time.time()) + 3600
            
            data_to_hash = f"{library_id}{api_key}{expiration_time}{guid}"
            signature = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
            
            return Response({
                'video_id': guid,
                'library_id': library_id,
                'authorization_signature': signature,
                'authorization_expire': expiration_time
            })
        
        return Response({'error': 'Failed to communicate with Bunny Stream.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            import time, hashlib
            # Save the GUID to the lesson so we know which video it belongs to
            lesson.video_id = guid
            lesson.save()
            
            library_id = os.environ.get('BUNNY_LIBRARY_ID')
            api_key = os.environ.get('BUNNY_API_KEY')
            expiration_time = int(time.time()) + 3600
            
            # Generate SHA256 signature for Bunny Stream TUS upload
            data_to_hash = f"{library_id}{api_key}{expiration_time}{guid}"
            signature = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
            
            return Response({
                'video_id': guid,
                'library_id': library_id,
                'authorization_signature': signature,
                'authorization_expire': expiration_time
            })
        
        return Response({'error': 'Failed to communicate with Bunny Stream.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    
    # We will use simple permissions: admin can manage, students can read/submit.
    def get_permissions(self):
        if self.action in ['save_all', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=['post'])
    def save_all(self, request, pk=None):
        quiz = self.get_object()
        data = request.data

        # Update quiz settings
        quiz.passing_score = data.get('passing_score', quiz.passing_score)
        quiz.max_attempts = data.get('max_attempts', quiz.max_attempts)
        quiz.time_limit_minutes = data.get('time_limit_minutes', quiz.time_limit_minutes)
        quiz.is_required = data.get('is_required', quiz.is_required)
        quiz.show_correct_answers = data.get('show_correct_answers', quiz.show_correct_answers)
        quiz.shuffle_questions = data.get('shuffle_questions', quiz.shuffle_questions)
        quiz.shuffle_answers = data.get('shuffle_answers', quiz.shuffle_answers)
        quiz.save()

        # Update questions & answers
        questions_data = data.get('questions', [])
        
        # We will delete all old questions and recreate them to ensure a clean state (simple approach)
        quiz.questions.all().delete()
        
        for q_data in questions_data:
            q = Question.objects.create(
                quiz=quiz,
                text=q_data.get('text', ''),
                question_type=q_data.get('question_type', 'multiple_choice'),
                order=q_data.get('order', 0)
            )
            answers_data = q_data.get('answers', [])
            for a_data in answers_data:
                Answer.objects.create(
                    question=q,
                    text=a_data.get('text', ''),
                    is_correct=a_data.get('is_correct', False)
                )

        return Response(QuizSerializer(quiz).data)

    # @action(detail=True, methods=['get'])
    # def student_view(self, request, pk=None):
    #     quiz = self.get_object()
    #     data = QuizSerializer(quiz).data

    #     # Hide correct answers from students
    #     for q in data.get('questions', []):
    #         for a in q.get('answers', []):
    #             a.pop('is_correct', None)
                
    #     user = request.user
    #     attempts_used = 0
    #     already_passed = False
        
    #     if user.is_authenticated:
    #         attempts = QuizAttempt.objects.filter(quiz=quiz, user=user)
    #         attempts_used = attempts.count()
    #         already_passed = attempts.filter(passed=True).exists()

    #     data['attempts_used'] = attempts_used
    #     data['already_passed'] = already_passed
    #     return Response(data)


    @action(detail=True, methods=['get'])
    def student_view(self, request, pk=None):
        try:
            quiz = self.get_object()
            
            serializer = QuizSerializer(quiz)
            data = serializer.data

            # Hide correct answers from students
            for question in data.get('questions', []):
                for answer in question.get('answers', []):
                    answer.pop('is_correct', None)

            # Add student progress
            attempts_used = 0
            already_passed = False

            if request.user.is_authenticated:
                attempts = QuizAttempt.objects.filter(quiz=quiz, user=request.user)
                attempts_used = attempts.count()
                already_passed = attempts.filter(passed=True).exists()

            data['attempts_used'] = attempts_used
            data['already_passed'] = already_passed

            return Response(data)

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("student_view failed for quiz_id=%s: %s", pk, error_msg)

            return Response({
                "error": "Failed to load quiz",
                "detail": str(e)
            }, status=500)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Must be logged in to submit a quiz.'}, status=status.HTTP_401_UNAUTHORIZED)
            
        submitted_answers = request.data.get('answers', {})
        time_taken = request.data.get('time_taken_seconds', 0)
        
        total_questions = quiz.questions.count()
        correct_count = 0
        correct_answers_dict = {}

        for q in quiz.questions.all():
            correct_ans = q.answers.filter(is_correct=True).first()
            if correct_ans:
                correct_answers_dict[str(q.id)] = correct_ans.id
                
            submitted_ans_id = submitted_answers.get(str(q.id))
            if correct_ans and submitted_ans_id is not None and int(submitted_ans_id) == correct_ans.id:
                correct_count += 1
                
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        passed = score >= quiz.passing_score
        
        attempt = QuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            score=score,
            passed=passed,
            time_taken_seconds=time_taken,
            selected_answers=submitted_answers
        )
        
        attempts_used = QuizAttempt.objects.filter(quiz=quiz, user=user).count()
        attempts_remaining = max(0, quiz.max_attempts - attempts_used) if quiz.max_attempts > 0 else None
        
        result = {
            'score': float(score),
            'passed': passed,
            'total_questions': total_questions,
            'correct_count': correct_count,
            'attempts_used': attempts_used,
            'attempts_remaining': attempts_remaining,
        }
        
        if quiz.show_correct_answers:
            result['correct_answers'] = correct_answers_dict
            
        return Response(result)

    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
        attempts = QuizAttempt.objects.filter(quiz=quiz, user=user).order_by('-attempted_at')
        serializer = QuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
