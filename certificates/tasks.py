from django.contrib.auth import get_user_model
from courses.models import Course
from .models import Certificate
from .generator import create_certificate_pdf
from datetime import datetime
from django_q.tasks import async_task
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


def generate_certificate_task(user_id, course_id):
    """
    Background task to generate a PDF certificate
    and queue certificate email sending.
    """

    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)

    # Create or fetch certificate
    cert, created = Certificate.objects.get_or_create(
        user=user,
        course=course
    )

    # Only generate if missing
    if created or not cert.pdf_file:

        # Generate PDF
        date_str = datetime.now().strftime("%B %d, %Y")

        pdf_file = create_certificate_pdf(
            user.get_full_name(),
            course.title,
            date_str,
            cert.certificate_id
        )

        # Save to storage (S3 / Supabase / Local)
        filename = (
            f"{user.id}_{course.slug}_certificate.pdf"
        )

        cert.pdf_file.save(
            filename,
            pdf_file
        )

        cert.save()

        logger.info(
            (
                "Generated certificate %s "
                "for user_id=%s course_id=%s; "
                "queueing email"
            ),
            cert.certificate_id,
            user.id,
            course.id
        )

        # Queue email task
        async_task(
            'emails.tasks.send_certificate_email_task',
            user.id,
            course.id
        )

        # Create notification
        from notifications.models import Notification

        Notification.objects.create(
            user=user,
            title="Certificate Ready!",
            message=(
                f"Congratulations! Your certificate for "
                f"{course.title} has been generated."
            ),
            notification_type='achievement'
        )

    return str(cert.certificate_id)