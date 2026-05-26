import json
import uuid
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Payment, Enrollment
from courses.models import Course
from .paystack import initialize_transaction, verify_signature, verify_transaction

class CheckoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        if not course.is_published:
            return Response({'error': 'This course is not available for enrollment yet.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a unique reference
        amount_in_kobo = int(course.price * 100)
        
        if amount_in_kobo == 0:
            Enrollment.objects.get_or_create(user=request.user, course=course)
            return Response({'free': True, 'message': 'Enrolled in free course.'})

        reference = f"LX-{uuid.uuid4().hex[:12].upper()}"

        # Initialize transaction with Paystack
        auth_url = initialize_transaction(request.user.email, amount_in_kobo, reference)

        if auth_url:
            # Create a pending payment record
            Payment.objects.create(
                user=request.user,
                course=course,
                amount=course.price,
                reference=reference,
                status='pending'
            )
            return Response({'authorization_url': auth_url})
        
        return Response({'error': 'Failed to initialize payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(views.APIView):
    permission_classes = [AllowAny] # Paystack servers don't have our auth tokens

    def post(self, request, *args, **kwargs):
        payload_body = request.body
        signature_header = request.headers.get('x-paystack-signature', '')

        # 1. Verify the signature to prevent spoofing
        if not verify_signature(payload_body, signature_header):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_data = json.loads(payload_body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Handle successful charges
        if event_data.get('event') == 'charge.success':
            data = event_data.get('data', {})
            reference = data.get('reference')
            paystack_id = data.get('id')

            try:
                payment = Payment.objects.get(reference=reference, status='pending')
            except Payment.DoesNotExist:
                # Payment already processed or reference is invalid
                return Response(status=status.HTTP_200_OK)

            # Update Payment status
            payment.status = 'success'
            payment.paystack_id = str(paystack_id)
            payment.save()

            # Auto-enroll the user
            Enrollment.objects.get_or_create(
                user=payment.user,
                course=payment.course
            )

        return Response(status=status.HTTP_200_OK)

class VerifyPaymentView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({'error': 'Reference is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if payment already processed
        try:
            payment = Payment.objects.get(reference=reference)
            if payment.status == 'success':
                return Response({'status': 'success', 'message': 'Payment already verified'})
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        # Verify with Paystack
        tx_data = verify_transaction(reference)
        if not tx_data:
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Update payment
        payment.status = 'success'
        payment.paystack_id = str(tx_data.get('id', ''))
        payment.save()

        # Auto-enroll
        Enrollment.objects.get_or_create(
            user=payment.user,
            course=payment.course
        )

        return Response({'status': 'success', 'message': 'Payment verified and enrolled'})

class MarkLessonCompleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson_id')
        try:
            from courses.models import Lesson
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is actually enrolled
        try:
            enrollment = Enrollment.objects.get(user=request.user, course=lesson.module.course)
            if not enrollment.is_active:
                return Response({'error': 'Your access to this course has been deactivated.'}, status=status.HTTP_403_FORBIDDEN)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Not enrolled in this course'}, status=status.HTTP_403_FORBIDDEN)

        from .models import LessonProgress
        # Mark lesson as complete
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_completed': True}
        )
        if not created and not progress.is_completed:
            progress.is_completed = True
            progress.save()

        # Recalculate course progress percentage
        total_lessons = Lesson.objects.filter(module__course=lesson.module.course).count()
        completed_lessons = LessonProgress.objects.filter(
            user=request.user, 
            lesson__module__course=lesson.module.course, 
            is_completed=True
        ).count()

        new_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        
        # Update enrollment progress
        enrollment.progress_percentage = new_percentage
        enrollment.save()

        # If 100%, trigger certificate generation
        if new_percentage == 100:
            from django_q.tasks import async_task
            async_task('certificates.tasks.generate_certificate_task', request.user.id, lesson.module.course.id)

        return Response({
            'status': 'success',
            'progress_percentage': new_percentage
        })

class MyEnrollmentsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Fetch active enrollments for the logged-in student
        enrollments = Enrollment.objects.filter(user=request.user, is_active=True).select_related('course')
        
        data = []
        for e in enrollments:
            data.append({
                'enrollment_id': e.id,
                'course_id': e.course.id,
                'course_title': e.course.title,
                'course_slug': e.course.slug,
                'course_thumbnail': e.course.thumbnail,
                'progress_percentage': e.progress_percentage,
                'enrolled_at': e.enrolled_at
            })
            
        return Response(data, status=status.HTTP_200_OK)


class CheckEnrollmentView(views.APIView):
    """Lightweight endpoint: GET /payments/check-enrollment/<course_id>/
    Returns {enrolled: true/false} with a single targeted query."""
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, *args, **kwargs):
        enrolled = Enrollment.objects.filter(
            user=request.user,
            course_id=course_id,
            is_active=True,
        ).exists()
        return Response({'enrolled': enrolled}, status=status.HTTP_200_OK)

