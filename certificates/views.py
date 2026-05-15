from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Certificate
from django.http import HttpResponse, Http404
import os

class MyCertificatesView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        certificates = Certificate.objects.filter(user=request.user).select_related('course')
        
        data = []
        for cert in certificates:
            data.append({
                'certificate_id': cert.certificate_id,
                'course_title': cert.course.title,
                'issued_at': cert.issued_at,
                'pdf_url': f'/api/certificates/{cert.certificate_id}/download/'
            })
            
        return Response(data, status=status.HTTP_200_OK)

class CertificateDownloadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, certificate_id, *args, **kwargs):
        try:
            cert = Certificate.objects.get(certificate_id=certificate_id, user=request.user)
        except Certificate.DoesNotExist:
            raise Http404("Certificate not found")

        # Check if file exists locally
        if cert.pdf_file and os.path.exists(cert.pdf_file.path):
            with open(cert.pdf_file.path, 'rb') as f:
                pdf_data = f.read()
        else:
            # File lost due to ephemeral disk, or not generated yet. Regenerate on the fly!
            from .generator import create_certificate_pdf
            date_str = cert.issued_at.strftime("%B %d, %Y")
            full_name = request.user.full_name or request.user.email
            content_file = create_certificate_pdf(full_name, cert.course.title, date_str, cert.certificate_id)
            pdf_data = content_file.read()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Certificate_{cert.certificate_id}.pdf"'
        return response
