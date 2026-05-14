from django.db import transaction
from django.contrib.auth import get_user_model
from courses.models import Course
from .models import Certificate
from .generator import create_certificate_pdf
from datetime import datetime

User = get_user_model()

def generate_certificate_task(user_id, course_id, force=False):
    """
    Background task to generate a PDF certificate and email it to the user.
    Executed by django-q2 worker.
    """
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)

    pdf_path = None

    # Create DB Record
    with transaction.atomic():
        cert, _ = Certificate.objects.select_for_update().get_or_create(user=user, course=course)

        # Skip email check if force is True so we can regenerate
        if cert.email_sent_at and not force:
            return str(cert.certificate_id)

        # Check if the file actually physically exists in the storage backend (S3/local)
        file_exists = False
        if cert.pdf_file and cert.pdf_file.name:
            try:
                file_exists = cert.pdf_file.storage.exists(cert.pdf_file.name)
            except Exception:
                file_exists = False

        if force or not file_exists:
            # Generate the PDF bytes
            date_str = datetime.now().strftime("%B %d, %Y")
            pdf_file = create_certificate_pdf(user.get_full_name() or user.email, course.title, date_str, cert.certificate_id)

            # Save to storage (S3/Local)
            filename = f"{user.id}_{course.slug}_certificate.pdf"
            
            # If the file exists but we are forcing, we can just save over it if S3 allows overwriting,
            # or delete it first. django-storages handles name collision by appending random strings if overwrite is false.
            # We explicitly want to overwrite, but let's just let Django handle it.
            cert.pdf_file.save(filename, pdf_file)

        # Using storage url instead of local path for emails
        pdf_path = cert.pdf_file.url if cert.pdf_file else None

    # Dispatch HTML Email with attachment after the DB transaction is committed
    from django_q.tasks import async_task
    async_task('emails.tasks.send_certificate_email_task', user.id, course.id, pdf_path)

    return str(cert.certificate_id)
