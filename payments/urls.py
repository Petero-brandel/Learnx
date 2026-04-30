from django.urls import path
from .views import CheckoutView, PaystackWebhookView, MarkLessonCompleteView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('webhook/paystack/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    path('progress/mark-complete/', MarkLessonCompleteView.as_view(), name='mark-lesson-complete'),
]
