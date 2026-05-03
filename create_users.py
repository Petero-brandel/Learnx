import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_users():
    if not User.objects.filter(email='admin@learnx.com').exists():
        User.objects.create_superuser(
            email='admin@learnx.com',
            password='adminpassword123',
            full_name='Admin User'
        )
        print("Superuser admin@learnx.com created.")
    else:
        print("Superuser already exists.")

    if not User.objects.filter(email='student@learnx.com').exists():
        User.objects.create_user(
            email='student@learnx.com',
            password='studentpassword123',
            full_name='Student User'
        )
        print("User student@learnx.com created.")
    else:
        print("User already exists.")

if __name__ == '__main__':
    create_users()
