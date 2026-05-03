from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from payments.models import Payment, Enrollment, LessonProgress
from courses.models import Course, Lesson

User = get_user_model()

class RevenueStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        successful_payments = Payment.objects.filter(status='success')

        # Totals
        today_rev = successful_payments.filter(created_at__gte=today_start).aggregate(Sum('amount'))['amount__sum'] or 0
        week_rev = successful_payments.filter(created_at__gte=week_start).aggregate(Sum('amount'))['amount__sum'] or 0
        month_rev = successful_payments.filter(created_at__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
        all_time_rev = successful_payments.aggregate(Sum('amount'))['amount__sum'] or 0

        # Revenue over time (Last 30 days)
        thirty_days_ago = today_start - timedelta(days=30)
        revenue_over_time = list(successful_payments.filter(created_at__gte=thirty_days_ago)
            .extra(select={'day': 'date(created_at)'})
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day'))

        # Revenue per course
        rev_per_course = list(successful_payments.values(course_title=F('course__title'))
            .annotate(total=Sum('amount'))
            .order_by('-total'))

        return Response({
            'revenue': {
                'today': today_rev,
                'this_week': week_rev,
                'this_month': month_rev,
                'all_time': all_time_rev
            },
            'revenue_over_time': revenue_over_time,
            'revenue_per_course': rev_per_course
        })

class UserStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        total_users = User.objects.count()
        
        # Signups over time (Last 30 days)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = today_start - timedelta(days=30)
        
        signups_over_time = list(User.objects.filter(date_joined__gte=thirty_days_ago)
            .extra(select={'day': 'date(date_joined)'})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day'))

        return Response({
            'total_students': total_users,
            'signups_over_time': signups_over_time
        })

class CoursePerformanceView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Enrollments per course (Popularity)
        enrollments_per_course = list(Enrollment.objects.values(course_title=F('course__title'))
            .annotate(total_enrollments=Count('id'))
            .order_by('-total_enrollments'))

        # Global Completion Rate
        total_enrollments = Enrollment.objects.count()
        if total_enrollments > 0:
            avg_completion = Enrollment.objects.aggregate(Sum('progress_percentage'))['progress_percentage__sum'] / total_enrollments
        else:
            avg_completion = 0

        return Response({
            'popular_courses': enrollments_per_course,
            'average_completion_rate': round(avg_completion, 2)
        })

class RecentActivityView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        recent_orders = Payment.objects.filter(status='success').order_by('-created_at')[:10]
        data = []
        for order in recent_orders:
            data.append({
                'id': order.id,
                'student': order.user.email,
                'course': order.course.title,
                'amount': order.amount,
                'date': order.created_at
            })
            
        return Response({
            'recent_orders': data
        })
