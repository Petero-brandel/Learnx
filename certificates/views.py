from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Certificate

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
                'pdf_url': cert.pdf_file.url if cert.pdf_file else None
            })
            
        return Response(data, status=status.HTTP_200_OK)
