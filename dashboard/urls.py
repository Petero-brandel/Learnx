from django.urls import path
from .analytics import RevenueStatsView, UserStatsView, CoursePerformanceView, RecentActivityView
from .management import ManualUserRegistrationView, ManualEnrollmentView, ManualCertificateView, BroadcastEmailView, EnrollmentManagementView

urlpatterns = [
    # Analytics
    path('stats/revenue/', RevenueStatsView.as_view(), name='dashboard-revenue-stats'),
    path('stats/users/', UserStatsView.as_view(), name='dashboard-user-stats'),
    path('stats/courses/', CoursePerformanceView.as_view(), name='dashboard-course-performance'),
    path('recent-activity/', RecentActivityView.as_view(), name='dashboard-recent-activity'),
    
    # Management
    path('management/register-user/', ManualUserRegistrationView.as_view(), name='dashboard-manual-register'),
    path('management/enroll/', ManualEnrollmentView.as_view(), name='dashboard-manual-enroll'),
    path('management/enrollments/', EnrollmentManagementView.as_view(), name='dashboard-enrollment-management'),
    path('management/generate-certificate/', ManualCertificateView.as_view(), name='dashboard-manual-certificate'),
    path('management/broadcast-email/', BroadcastEmailView.as_view(), name='dashboard-broadcast-email'),
]
