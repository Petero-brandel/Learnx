import logging
import os

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from courses.models import Course
from certificates.models import Certificate

User = get_user_model()
logger = logging.getLogger(__name__)

FRONTEND_URL = os.environ.get(
    'FRONTEND_URL',
    'http://localhost:3000'
).rstrip('/')


def send_html_email(
    subject,
    template_name,
    context,
    recipient_list,
    attachment_file=None
):
    """
    Utility function to send a multi-alternative
    email (HTML + Plain text fallback)
    """

    logger.info(
        "Sending email subject=%s recipients=%s template=%s",
        subject,
        recipient_list,
        template_name
    )

    html_content = render_to_string(
        f'emails/{template_name}',
        context
    )

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )

    email.attach_alternative(
        html_content,
        "text/html"
    )

    # ---------------------------------------------------
    # ATTACH PDF FROM STORAGE (SUPABASE S3 / LOCAL)
    # ---------------------------------------------------

    if attachment_file:
        try:
            attachment_file.open('rb')

            email.attach(
                'Certificate_of_Completion.pdf',
                attachment_file.read(),
                'application/pdf'
            )

            attachment_file.close()

        except Exception:
            logger.exception(
                (
                    "Attachment failed "
                    "subject=%s recipients=%s"
                ),
                subject,
                recipient_list
            )

    # ---------------------------------------------------
    # SEND EMAIL
    # ---------------------------------------------------

    try:
        sent_count = email.send(
            fail_silently=False
        )

        logger.info(
            (
                "Email sent subject=%s "
                "recipients=%s sent_count=%s "
                "backend=%s"
            ),
            subject,
            recipient_list,
            sent_count,
            settings.EMAIL_BACKEND
        )

        return sent_count

    except Exception:
        logger.exception(
            (
                "Email send failed subject=%s "
                "recipients=%s backend=%s"
            ),
            subject,
            recipient_list,
            settings.EMAIL_BACKEND
        )

        raise


def send_welcome_email_task(user_id):

    user = User.objects.get(id=user_id)

    login_url = f"{FRONTEND_URL}/login"

    send_html_email(
        subject="Welcome to Bluedemy!",
        template_name="welcome.html",
        context={
            'user': user,
            'login_url': login_url
        },
        recipient_list=[user.email]
    )


def send_purchase_email_task(user_id, course_id):

    user = User.objects.get(id=user_id)

    course = Course.objects.get(id=course_id)

    course_url = (
        f"{FRONTEND_URL}/courses/{course.slug}"
    )

    send_html_email(
        subject="Course Unlocked!",
        template_name="purchase.html",
        context={
            'user': user,
            'course': course,
            'course_url': course_url
        },
        recipient_list=[user.email]
    )


def send_certificate_email_task(
    user_id,
    course_id
):

    user = User.objects.get(id=user_id)

    course = Course.objects.get(id=course_id)

    cert = Certificate.objects.get(
        user=user,
        course=course
    )

    send_html_email(
        subject="Certificate Ready!",
        template_name="certificate.html",
        context={
            'user': user,
            'course': course
        },
        recipient_list=[user.email],
        attachment_file=cert.pdf_file
    )


def send_verification_email_task(user_id):

    user = User.objects.get(id=user_id)

    verify_url = (
        f"{FRONTEND_URL}"
        f"/verify-email?token="
        f"{user.verification_token}"
    )

    send_html_email(
        subject="Verify your Bluedemy account email",
        template_name="verification.html",
        context={
            'user': user,
            'verify_url': verify_url
        },
        recipient_list=[user.email]
    )


def send_password_reset_email_task(
    user_id,
    uidb64,
    token
):

    user = User.objects.get(id=user_id)

    reset_url = (
        f"{FRONTEND_URL}"
        f"/reset-password?"
        f"uid={uidb64}&token={token}"
    )

    send_html_email(
        subject="Reset your Bluedemy password",
        template_name="password_reset.html",
        context={
            'user': user,
            'reset_url': reset_url
        },
        recipient_list=[user.email]
    )