from django.urls import path
from .views import MyCertificatesView, CertificateDownloadView, CertificatePreviewView

urlpatterns = [
    path('my-certificates/', MyCertificatesView.as_view(), name='my-certificates'),
    path('<uuid:certificate_id>/download/', CertificateDownloadView.as_view(), name='certificate-download'),
    path('<uuid:certificate_id>/preview/', CertificatePreviewView.as_view(), name='certificate-preview'),
]
