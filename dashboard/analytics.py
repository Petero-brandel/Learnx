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

        # Revenue over time
        period = request.query_params.get('period', '7d')
        if period == '1y':
            start_date = today_start - timedelta(days=365)
            from django.db.models.functions import TruncMonth
            rev_qs = list(successful_payments.filter(created_at__gte=start_date)
                .annotate(month=TruncMonth('created_at'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month'))
            
            revenue_over_time = []
            for item in rev_qs:
                if item['month']:
                    revenue_over_time.append({
                        'day': item['month'].strftime('%Y-%m-%d'),
                        'total': item['total']
                    })
        else:
            days_map = {'7d': 7, '14d': 14, '30d': 30}
            days = days_map.get(period, 7)
            start_date = today_start - timedelta(days=days-1)
            revenue_over_time = list(successful_payments.filter(created_at__gte=start_date)
                .extra(select={'day': 'date(created_at)'})
                .values('day')
                .annotate(total=Sum('amount'))
                .order_by('day'))

        # Revenue per course
        rev_per_course_qs = list(successful_payments.values(course_title_raw=F('course__title'))
            .annotate(total=Sum('amount'))
            .order_by('-total'))
            
        rev_per_course = []
        for item in rev_per_course_qs:
            rev_per_course.append({
                'course_title': item['course_title_raw'] or 'Deleted Course',
                'total': item['total']
            })

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
        
        # Signups over time
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period = request.query_params.get('period', '7d')
        
        if period == '1y':
            start_date = today_start - timedelta(days=365)
            from django.db.models.functions import TruncMonth
            signups_qs = list(User.objects.filter(date_joined__gte=start_date)
                .annotate(month=TruncMonth('date_joined'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month'))
            
            signups_over_time = []
            for item in signups_qs:
                if item['month']:
                    signups_over_time.append({
                        'day': item['month'].strftime('%Y-%m-%d'),
                        'count': item['count']
                    })
        else:
            days_map = {'7d': 7, '14d': 14, '30d': 30}
            days = days_map.get(period, 7)
            start_date = today_start - timedelta(days=days-1)
            
            signups_over_time = list(User.objects.filter(date_joined__gte=start_date)
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
        recent_orders = Payment.objects.filter(status='success').order_by('-created_at')[:50]
        data = []
        for order in recent_orders:
            data.append({
                'id': order.id,
                'student': order.user.email,
                'course': order.course.title if order.course else 'Deleted Course',
                'amount': order.amount,
                'date': order.created_at
            })
            
        return Response({
            'recent_orders': data
        })
