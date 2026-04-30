from django.urls import path
from .views import CheckoutView, PaystackWebhookView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('webhook/paystack/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
