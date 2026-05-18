from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .models import Certificate
from .generator import create_certificate_pdf, create_certificate_preview
from datetime import datetime


class MyCertificatesView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        certificates = Certificate.objects.filter(user=request.user).select_related('course')
        
        data = []
        for cert in certificates:
            data.append({
                'certificate_id': str(cert.certificate_id),
                'course_title': cert.course.title,
                'issued_at': cert.issued_at,
            })
            
        return Response(data, status=status.HTTP_200_OK)


class CertificateDownloadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, certificate_id, *args, **kwargs):
        try:
            cert = Certificate.objects.select_related('course', 'user').get(
                certificate_id=certificate_id,
                user=request.user
            )
        except Certificate.DoesNotExist:
            return Response({'error': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate PDF on the fly
        student_name = cert.user.full_name if cert.user.full_name else "Student"
        date_str = cert.issued_at.strftime("%B %d, %Y")
        pdf_content = create_certificate_pdf(student_name, cert.course.title, date_str, cert.certificate_id)

        # Stream as downloadable PDF
        response = HttpResponse(pdf_content.read(), content_type='application/pdf')
        safe_title = cert.course.title.replace(' ', '_').replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="Certificate_{safe_title}.pdf"'
        return response


class CertificatePreviewView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, certificate_id, *args, **kwargs):
        try:
            cert = Certificate.objects.select_related('course', 'user').get(
                certificate_id=certificate_id,
                user=request.user
            )
        except Certificate.DoesNotExist:
            return Response({'error': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate preview image on the fly
        student_name = cert.user.full_name if cert.user.full_name else "Student"
        date_str = cert.issued_at.strftime("%B %d, %Y")
        preview_buffer = create_certificate_preview(student_name, cert.course.title, date_str, cert.certificate_id)

        response = HttpResponse(preview_buffer.read(), content_type='image/jpeg')
        response['Cache-Control'] = 'public, max-age=3600'
        return response
