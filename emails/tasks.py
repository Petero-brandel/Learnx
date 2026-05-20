from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
import os
from courses.models import Course

User = get_user_model()

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')

def send_html_email(subject, template_name, context, recipient_list, attachment_path=None):
    """
    Utility function to send a multi-alternative email (HTML + Plain text fallback)
    """
    html_content = render_to_string(f'emails/{template_name}', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )
    email.attach_alternative(html_content, "text/html")
    
    # Attach PDF if provided
    if attachment_path:
        try:
            with open(attachment_path, 'rb') as pdf_file:
                email.attach('Certificate_of_Completion.pdf', pdf_file.read(), 'application/pdf')
        except FileNotFoundError:
            print(f"Warning: Attachment not found at {attachment_path}")
            
    email.send(fail_silently=True)

def send_welcome_email_task(user_id):
    user = User.objects.get(id=user_id)
    login_url = f"{FRONTEND_URL}/login"
    
    send_html_email(
        subject="Welcome to LearnX! 🎉",
        template_name="welcome.html",
        context={'user': user, 'login_url': login_url},
        recipient_list=[user.email]
    )

def send_purchase_email_task(user_id, course_id):
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    course_url = f"{FRONTEND_URL}/courses/{course.slug}"
    
    send_html_email(
        subject="Course Unlocked! 🚀",
        template_name="purchase.html",
        context={'user': user, 'course': course, 'course_url': course_url},
        recipient_list=[user.email]
    )

def send_certificate_email_task(user_id, course_id, pdf_path):
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    
    send_html_email(
        subject="Certificate Ready! 🏆",
        template_name="certificate.html",
        context={'user': user, 'course': course},
        recipient_list=[user.email],
        attachment_path=pdf_path
    )

def send_verification_email_task(user_id):
    user = User.objects.get(id=user_id)
    verify_url = f"{FRONTEND_URL}/verify-email?token={user.verification_token}"
    
    send_html_email(
        subject="Verify your LearnX account email",
        template_name="verification.html",
        context={'user': user, 'verify_url': verify_url},
        recipient_list=[user.email]
    )

def send_password_reset_email_task(user_id, uidb64, token):
    user = User.objects.get(id=user_id)
    reset_url = f"{FRONTEND_URL}/reset-password?uid={uidb64}&token={token}"
    
    send_html_email(
        subject="Reset your LearnX password",
        template_name="password_reset.html",
        context={'user': user, 'reset_url': reset_url},
        recipient_list=[user.email]
    )
