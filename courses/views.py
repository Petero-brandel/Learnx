import os
import hashlib
import time
import random
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from .models import Course, Module, Lesson, Quiz, Question, Answer
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, 
    ModuleSerializer, LessonSerializer, LessonReorderSerializer,
    QuizSerializer, QuestionSerializer, AnswerSerializer,
    StudentQuizSerializer, QuizBulkSaveSerializer, QuizSubmissionSerializer,
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
        if self.request.user.is_staff:
            return Course.objects.all()
        return Course.objects.filter(is_published=True)

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
            library_id = os.environ.get('BUNNY_LIBRARY_ID')
            api_key = os.environ.get('BUNNY_API_KEY')
            expiration_time = int(time.time()) + 3600
            
            signature_str = f"{library_id}{api_key}{expiration_time}{guid}"
            signature = hashlib.sha256(signature_str.encode()).hexdigest()

            return Response({
                'video_id': guid,
                'library_id': library_id,
                'authorization_signature': signature,
                'authorization_expire': expiration_time
            })
        
        return Response({'error': 'Failed to communicate with Bunny Stream.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Quiz Views ──────────────────────────────────────────────

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def save_all(self, request, pk=None):
        """
        Bulk-saves the entire quiz structure (settings + questions + answers) in one request.
        Replaces all existing questions/answers with the new payload.
        """
        quiz = self.get_object()
        serializer = QuizBulkSaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        with transaction.atomic():
            # Update quiz settings
            quiz.passing_score = data['passing_score']
            quiz.max_attempts = data['max_attempts']
            quiz.time_limit_minutes = data['time_limit_minutes']
            quiz.is_required = data['is_required']
            quiz.show_correct_answers = data['show_correct_answers']
            quiz.shuffle_questions = data['shuffle_questions']
            quiz.shuffle_answers = data['shuffle_answers']
            quiz.save()

            # Delete all existing questions (cascades to answers)
            quiz.questions.all().delete()

            # Re-create questions and answers from payload
            for q_data in data['questions']:
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data['text'],
                    question_type=q_data.get('question_type', 'multiple_choice'),
                    order=q_data.get('order', 0),
                )
                for a_data in q_data.get('answers', []):
                    Answer.objects.create(
                        question=question,
                        text=a_data['text'],
                        is_correct=a_data.get('is_correct', False),
                    )

        # Return the updated quiz
        quiz.refresh_from_db()
        return Response(QuizSerializer(quiz).data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def student_view(self, request, pk=None):
        """
        Returns the quiz without is_correct on answers. Shuffles if configured.
        Also includes attempts_used count.
        """
        quiz = self.get_object()

        # Verify enrollment
        from payments.models import Enrollment
        lesson = quiz.lesson
        course = lesson.module.course
        if not request.user.is_staff:
            if not Enrollment.objects.filter(user=request.user, course=course, is_active=True).exists():
                return Response({'error': 'Not enrolled in this course.'}, status=status.HTTP_403_FORBIDDEN)

        data = StudentQuizSerializer(quiz).data

        # Shuffle if configured
        if quiz.shuffle_questions:
            random.shuffle(data['questions'])
        if quiz.shuffle_answers:
            for q in data['questions']:
                random.shuffle(q['answers'])

        # Add attempts info
        from payments.models import QuizAttempt
        attempts_used = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
        data['attempts_used'] = attempts_used

        # Check if already passed
        data['already_passed'] = QuizAttempt.objects.filter(
            user=request.user, quiz=quiz, passed=True
        ).exists()

        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """
        Student submits quiz answers. Calculates score, creates attempt,
        and auto-marks lesson complete if passed (or if not required).
        """
        quiz = self.get_object()

        # Verify enrollment
        from payments.models import Enrollment, LessonProgress, QuizAttempt
        lesson = quiz.lesson
        course = lesson.module.course

        try:
            enrollment = Enrollment.objects.get(user=request.user, course=course)
            if not enrollment.is_active:
                return Response({'error': 'Your access to this course has been deactivated.'}, status=status.HTTP_403_FORBIDDEN)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Not enrolled in this course.'}, status=status.HTTP_403_FORBIDDEN)

        # Check max attempts
        attempts_used = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
        if quiz.max_attempts > 0 and attempts_used >= quiz.max_attempts:
            return Response({
                'error': 'Maximum attempts reached.',
                'attempts_used': attempts_used,
                'max_attempts': quiz.max_attempts,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate submission
        serializer = QuizSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submitted_answers = serializer.validated_data['answers']
        started_at = serializer.validated_data.get('started_at')
        time_taken_seconds = serializer.validated_data.get('time_taken_seconds', 0)

        # Check time limit
        if quiz.time_limit_minutes > 0 and started_at:
            time_limit_seconds = quiz.time_limit_minutes * 60
            # Allow 30 seconds of grace for network latency
            if time_taken_seconds > (time_limit_seconds + 30):
                return Response({'error': 'Time limit exceeded.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate score
        questions = quiz.questions.prefetch_related('answers').all()
        total = questions.count()
        if total == 0:
            return Response({'error': 'Quiz has no questions.'}, status=status.HTTP_400_BAD_REQUEST)

        correct = 0
        correct_answers_map = {}

        for question in questions:
            correct_answer = question.answers.filter(is_correct=True).first()
            if correct_answer:
                correct_answers_map[str(question.id)] = correct_answer.id
                submitted_answer_id = submitted_answers.get(str(question.id))
                if submitted_answer_id == correct_answer.id:
                    correct += 1

        score = int((correct / total) * 100)
        passed = score >= quiz.passing_score

        # Create attempt record
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
            answers=submitted_answers,
            started_at=started_at,
            time_taken_seconds=time_taken_seconds,
        )

        # Mark lesson complete if passed (or if quiz is not required)
        should_mark_complete = passed or not quiz.is_required
        if should_mark_complete:
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson,
                defaults={'is_completed': True}
            )
            if not created and not progress.is_completed:
                progress.is_completed = True
                progress.save()

            # Recalculate course progress percentage
            total_lessons = Lesson.objects.filter(module__course=course).count()
            completed_lessons = LessonProgress.objects.filter(
                user=request.user,
                lesson__module__course=course,
                is_completed=True
            ).count()

            new_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
            enrollment.progress_percentage = new_percentage
            enrollment.save()

            # If 100%, trigger certificate generation
            if new_percentage == 100:
                from certificates.models import Certificate
                should_queue = False

                with transaction.atomic():
                    cert, _ = Certificate.objects.select_for_update().get_or_create(
                        user=request.user,
                        course=course,
                    )
                    if not cert.pdf_file and not cert.generation_requested_at:
                        cert.generation_requested_at = timezone.now()
                        cert.save(update_fields=['generation_requested_at'])
                        should_queue = True

                if should_queue:
                    from django_q.tasks import async_task
                    async_task('certificates.tasks.generate_certificate_task', request.user.id, course.id)

        # Build response
        response_data = {
            'score': score,
            'passed': passed,
            'total_questions': total,
            'correct_count': correct,
            'attempts_used': attempts_used + 1,
            'attempts_remaining': (quiz.max_attempts - attempts_used - 1) if quiz.max_attempts > 0 else None,
        }

        # Only include correct answers if configured
        if quiz.show_correct_answers:
            response_data['correct_answers'] = correct_answers_map

        return Response(response_data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def attempts(self, request, pk=None):
        """
        Returns the user's past attempts for this quiz.
        """
        quiz = self.get_object()
        from payments.models import QuizAttempt
        attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
        data = [{
            'id': a.id,
            'score': a.score,
            'passed': a.passed,
            'attempted_at': a.attempted_at,
            'time_taken_seconds': a.time_taken_seconds,
        } for a in attempts]
        return Response(data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAdminUser]
