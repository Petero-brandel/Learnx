from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.URLField(max_length=1024, blank=True, null=True) # URL from Bunny Stream or Google Auth
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Trigger notifications on new user registration
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_welcome_notification(sender, instance, created, **kwargs):
    if created:
        from notifications.models import Notification
        # 1. Welcome the student
        Notification.objects.create(
            user=instance,
            title="Welcome to LearnX! 🎉",
            message="We are thrilled to have you here. Browse our courses and start learning today!",
            notification_type='system'
        )
        
        # Dispatch HTML Email
        from django_q.tasks import async_task
        async_task('emails.tasks.send_welcome_email_task', instance.id)
        
        # 2. Notify the Admin (Coach Izu)
        admins = CustomUser.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="New Student Registration",
                message=f"{instance.email} just joined the platform!",
                notification_type='system'
            )
