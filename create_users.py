import os
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

def create_users():
    # 1. Create Superuser (Admin)
    if not User.objects.filter(email='admin@bluedemy.org').exists():
        User.objects.create_superuser(
            email='admin@bluedemy.org',
            password='password123',
            full_name='Admin User'
        )
        logger.info("Superuser admin@bluedemy.org created.")
    else:
        logger.info("Superuser already exists.")

    # 2. Create Regular Student
    if not User.objects.filter(email='student@bluedemy.org').exists():
        User.objects.create_user(
            email='student@bluedemy.org',
            password='password123',
            full_name='Test Student'
        )
        logger.info("User student@bluedemy.org created.")
    else:
        logger.info("User already exists.")

if __name__ == '__main__':
    create_users()
