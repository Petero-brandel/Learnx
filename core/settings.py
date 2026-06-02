"""
Django settings for core project.
"""

from pathlib import Path
import os
import urllib.parse
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# ---------------------------------------------------
# BASE DIR
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------
# LOAD ENV
# ---------------------------------------------------

load_dotenv(os.path.join(BASE_DIR, ".env"))

# ---------------------------------------------------
# DATABASE URL CONSTRUCTION
# ---------------------------------------------------

if "DATABASE_URL" not in os.environ and "DB_HOST" in os.environ:
    db_user = urllib.parse.quote_plus(os.environ.get("DB_USER", ""))
    db_password = urllib.parse.quote_plus(os.environ.get("DB_PASSWORD", ""))

    os.environ["DATABASE_URL"] = (
        f"postgres://{db_user}:{db_password}"
        f"@{os.environ.get('DB_HOST', '')}"
        f":{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ.get('DB_NAME', '')}"
    )

    if "DB_SSLMODE" in os.environ:
        os.environ["DATABASE_URL"] += (
            f"?sslmode={os.environ.get('DB_SSLMODE')}"
        )

# ---------------------------------------------------
# SECURITY
# ---------------------------------------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this-in-production"
)

DEBUG = os.environ.get("DEBUG", "False").lower() in [
    "true",
    "1",
    "yes"
]

# ---------------------------------------------------
# ALLOWED HOSTS
# ---------------------------------------------------

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "learnx-app.fly.dev",
    ".fly.dev",
]

# ---------------------------------------------------
# FLY.IO / HTTPS SETTINGS
# ---------------------------------------------------

if os.environ.get("FLY_APP_NAME"):

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SECURE_SSL_REDIRECT = False

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = int(
        os.environ.get("SECURE_HSTS_SECONDS", "31536000")
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third Party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_q",
    "storages",

    # Local Apps
    "accounts",
    "courses",
    "payments",
    "certificates",
    "dashboard",
    "notifications",
    "emails",
]

# ---------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ---------------------------------------------------
# CORS
# ---------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    "https://bluedemy.org",
    "https://www.bluedemy.org",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------
# CSRF TRUSTED ORIGINS
# ---------------------------------------------------

CSRF_TRUSTED_ORIGINS = [
    "https://bluedemy.org",
    "https://www.bluedemy.org",
]

# ---------------------------------------------------
# URLS / WSGI
# ---------------------------------------------------

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------
# TEMPLATES
# ---------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------
# DATABASE
# ---------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
        ),
        conn_max_age=600,
        ssl_require=False,
    )
}

# ---------------------------------------------------
# AUTH USER MODEL
# ---------------------------------------------------

AUTH_USER_MODEL = "accounts.CustomUser"

# ---------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# ---------------------------------------------------
# SIMPLE JWT
# ---------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# ---------------------------------------------------
# DJANGO Q
# ---------------------------------------------------

Q_CLUSTER = {
    "name": "BluedemyCluster",
    "workers": 4,
    "recycle": 500,
    "timeout": 60,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q",
    "orm": "default",
    "max_attempts": 3,
}

# ---------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# ---------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# ---------------------------------------------------
# STATIC FILES
# ---------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------
# STORAGE / MEDIA
# ---------------------------------------------------

if os.environ.get("SUPABASE_S3_ACCESS_KEY_ID"):

    AWS_ACCESS_KEY_ID = os.environ.get(
        "SUPABASE_S3_ACCESS_KEY_ID"
    )

    AWS_SECRET_ACCESS_KEY = os.environ.get(
        "SUPABASE_S3_SECRET_ACCESS_KEY"
    )

    AWS_STORAGE_BUCKET_NAME = os.environ.get(
        "SUPABASE_S3_BUCKET_NAME",
        "learnx-bucket"
    )

    AWS_S3_ENDPOINT_URL = os.environ.get(
        "SUPABASE_S3_ENDPOINT_URL"
    )

    AWS_S3_REGION_NAME = os.environ.get(
        "SUPABASE_S3_REGION_NAME",
        "eu-central-1"
    )

    AWS_S3_SIGNATURE_VERSION = "s3v4"

    AWS_S3_FILE_OVERWRITE = False

    AWS_QUERYSTRING_AUTH = True

    AWS_QUERYSTRING_EXPIRE = 3600

    STORAGES = {
        "default": {
            "BACKEND": (
                "storages.backends.s3boto3.S3Boto3Storage"
            ),
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

else:

    MEDIA_URL = "/media/"

    MEDIA_ROOT = BASE_DIR / "media"

    STORAGES = {
        "default": {
            "BACKEND": (
                "django.core.files.storage."
                "FileSystemStorage"
            ),
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

# ---------------------------------------------------
# EMAIL
# ---------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.resend.com"

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = "resend"

EMAIL_HOST_PASSWORD = os.environ.get(
    "RESEND_API_KEY",
    ""
)

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "noreply@contact.bluedemy.org"
)

# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {processName} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.core.mail": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "emails": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django_q": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "payments": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "courses": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "certificates": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "dashboard": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ---------------------------------------------------
# DEFAULT PRIMARY KEY
# ---------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"