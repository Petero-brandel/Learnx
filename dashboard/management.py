from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django_q.tasks import async_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count

from payments.models import Payment, Enrollment
from courses.models import Course

User = get_user_model()


class StudentListView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        students = (
            User.objects
            .filter(is_staff=False, is_superuser=False)
            .annotate(enrollment_count=Count('enrollment'))
            .order_by('-date_joined')
        )
        data = []
        for s in students:
            data.append({
                'id': s.id,
                'email': s.email,
                'full_name': s.full_name or '',
                'date_joined': s.date_joined,
                'is_active': s.is_active,
                'is_email_verified': s.is_email_verified,
                'enrollment_count': s.enrollment_count,
            })
        return Response(data)

class ManualUserRegistrationView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'User already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
        return Response({'status': 'User created successfully', 'user_id': user.id}, status=status.HTTP_201_CREATED)

class ManualEnrollmentView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')

        try:
            user = User.objects.get(id=user_id)
            course = Course.objects.get(id=course_id)
        except (User.DoesNotExist, Course.DoesNotExist):
            return Response({'error': 'Invalid user or course ID.'}, status=status.HTTP_404_NOT_FOUND)

        # Log a manual payment record so it shows up in revenue stats
        Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            reference=f"MANUAL-{user.id}-{course.id}",
            status='success'
        )

        Enrollment.objects.get_or_create(user=user, course=course)
        
        return Response({'status': f'User {user.email} successfully enrolled in {course.title}.'}, status=status.HTTP_200_OK)

class ManualCertificateView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')
        
        # Force the certificate task to run immediately
        async_task('certificates.tasks.generate_certificate_task', user_id, course_id)
        
        return Response({'status': 'Certificate generation queued in the background.'}, status=status.HTTP_200_OK)

def bulk_email_worker(subject, body, user_ids):
    users = User.objects.filter(id__in=user_ids)
    recipient_list = [u.email for u in users]
    
    # Send email
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )
    
    # Create in-app notifications
    from notifications.models import Notification
    notifications = [
        Notification(
            user=user,
            title=subject,
            message=body,
            notification_type='broadcast'
        ) for user in users
    ]
    Notification.objects.bulk_create(notifications)

class BroadcastEmailView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        subject = request.data.get('subject')
        body = request.data.get('body')
        target_audience = request.data.get('target_audience') # 'all' or specific course_id
        
        if not subject or not body:
            return Response({'error': 'Subject and body are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if target_audience == 'all':
            user_ids = list(User.objects.values_list('id', flat=True))
        else:
            try:
                course_id = int(target_audience)
                user_ids = list(Enrollment.objects.filter(course_id=course_id).values_list('user_id', flat=True))
            except ValueError:
                return Response({'error': 'Invalid target audience.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user_ids:
            return Response({'error': 'No users found for the target audience.'}, status=status.HTTP_400_BAD_REQUEST)

        # Queue the mass email to avoid blocking the API
        async_task('dashboard.management.bulk_email_worker', subject, body, user_ids)
        
        return Response({'status': f'Broadcast queued for {len(user_ids)} students.'}, status=status.HTTP_200_OK)

class EnrollmentManagementView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # List all enrollments with student and course info
        enrollments = Enrollment.objects.select_related('user', 'course').all().order_by('-enrolled_at')
        data = []
        for e in enrollments:
            data.append({
                'id': e.id,
                'student_email': e.user.email,
                'course_title': e.course.title,
                'enrolled_at': e.enrolled_at,
                'progress': e.progress_percentage,
                'is_active': e.is_active
            })
        return Response(data)

    def patch(self, request, *args, **kwargs):
        # Toggle activation status
        enrollment_id = request.data.get('enrollment_id')
        is_active = request.data.get('is_active')

        if enrollment_id is None or is_active is None:
            return Response({'error': 'enrollment_id and is_active are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            enrollment.is_active = bool(is_active)
            enrollment.save()
            return Response({'status': f"Enrollment {'activated' if enrollment.is_active else 'deactivated'} successfully."})
        except Enrollment.DoesNotExist:
            return Response({'error': 'Enrollment not found.'}, status=status.HTTP_404_NOT_FOUND)

