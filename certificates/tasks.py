from django.contrib.auth import get_user_model
from courses.models import Course
from .models import Certificate
from .generator import create_certificate_pdf
from datetime import datetime

User = get_user_model()

def generate_certificate_task(user_id, course_id):
    """
    Background task to generate a PDF certificate and email it to the user.
    Executed by django-q2 worker.
    """
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    
    # Create DB Record
    cert, created = Certificate.objects.get_or_create(user=user, course=course)
    
    if created or not cert.pdf_file:
        # Generate the PDF bytes
        date_str = datetime.now().strftime("%B %d, %Y")
        pdf_file = create_certificate_pdf(user.get_full_name() or user.email, course.title, date_str, cert.certificate_id)
        
        # Save to storage (S3/Local)
        filename = f"{user.id}_{course.slug}_certificate.pdf"
        cert.pdf_file.save(filename, pdf_file)
        
        # TODO: Send Email via Resend with PDF attached
        # send_certificate_email(user.email, cert.pdf_file.url)
        
    return str(cert.certificate_id)
