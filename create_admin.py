#!/usr/bin/env python
"""Create a superuser directly via Django ORM."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

EMAIL = 'admin@learnx.com'
PASSWORD = 'learnxadmin001'
FULL_NAME = 'Admin'

if User.objects.filter(email=EMAIL).exists():
    print(f'Superuser {EMAIL} already exists.')
else:
    user = User.objects.create_superuser(
        email=EMAIL,
        full_name=FULL_NAME,
        password=PASSWORD,
    )
    print(f'Superuser created successfully!')
    print(f'  Email: {EMAIL}')
    print(f'  Password: {PASSWORD}')
