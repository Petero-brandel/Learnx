from django.urls import path
from .views import MyCertificatesView

urlpatterns = [
    path('my-certificates/', MyCertificatesView.as_view(), name='my-certificates'),
]
