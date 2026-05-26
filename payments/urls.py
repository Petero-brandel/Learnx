from django.urls import path
from .views import CheckoutView, PaystackWebhookView, MarkLessonCompleteView, MyEnrollmentsView, VerifyPaymentView, CheckEnrollmentView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/paystack/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    path('progress/mark-complete/', MarkLessonCompleteView.as_view(), name='mark-lesson-complete'),
    path('my-enrollments/', MyEnrollmentsView.as_view(), name='my-enrollments'),
    path('check-enrollment/<int:course_id>/', CheckEnrollmentView.as_view(), name='check-enrollment'),
]

