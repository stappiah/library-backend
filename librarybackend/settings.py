"""
Django settings for librarybackend project.

This settings module is designed to work for both local development
and production. It reads configuration from environment variables via
`python-decouple` (`config`).

Features:
- `dj-database-url` for DATABASE_URL parsing
- Conditional Cloudinary support (only enabled when credentials and
  packages are present)
- WhiteNoise for static serving in simple deployments
- Secure defaults applied when `DEBUG=False`

Keep secrets (SECRET_KEY, CLOUDINARY_* etc.) out of version control.
"""

from pathlib import Path
import os
import importlib.util
from decouple import config
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
import logging
from urllib.parse import urlparse

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------- Core settings --------------------
# SECURITY: define SECRET_KEY in environment or .env (no default in VCS)
SECRET_KEY = config("SECRET_KEY", default="")

# DEBUG should be False in production
DEBUG = config("DEBUG", default=False, cast=bool)

# Hosts (load from env, comma-separated)
ALLOWED_HOSTS = [h.strip() for h in config("ALLOWED_HOSTS", default="library-backend-a3sj.onrender.com,localhost").split(",") if h.strip()]

# Ensure SECRET_KEY is provided in production
if not DEBUG and not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG=False")

# -------------------- Installed apps & middleware --------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "account",
    "base",
]

# Helper to check optional packages
def _package_available(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None

# Add optional Cloudinary apps only when packages exist
if _package_available("cloudinary") and _package_available("cloudinary_storage"):
    INSTALLED_APPS += ["cloudinary", "cloudinary_storage"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise early to serve static files when appropriate
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "librarybackend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "librarybackend.wsgi.application"

# -------------------- Database --------------------
DATABASE_URL = config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=config("DATABASE_CONN_MAX_AGE", default=600, cast=int),
        ssl_require=config("DATABASE_SSL_REQUIRE", default=False, cast=bool),
    )
}

# Do not allow SQLite in production by default
if not DEBUG and (DATABASE_URL.startswith("sqlite:") or DATABASE_URL.endswith("db.sqlite3")):
    raise ImproperlyConfigured("Using SQLite in production is not supported. Set a proper DATABASE_URL.")

# -------------------- Auth & password validators --------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------- Internationalization --------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# -------------------- Static & Media --------------------
STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = Path(config("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))
STATICFILES_DIRS = [BASE_DIR / "static"]

# -------------------- Logging --------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
}

# -------------------- REST Framework --------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": config("PAGE_SIZE", default=12, cast=int),
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("THROTTLE_ANON_RATE", default="100/hour"),
        "user": config("THROTTLE_USER_RATE", default="1000/hour"),
    },
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append("rest_framework.renderers.BrowsableAPIRenderer")

# -------------------- CORS & CSRF --------------------
CORS_ALLOWED_ORIGINS = [o.strip() for o in config("CORS_ALLOWED_ORIGINS", default=
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:8000").split(",") if o.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in config("CSRF_TRUSTED_ORIGINS", default="").split(",") if o.strip()]

CORS_ALLOW_CREDENTIALS = True

# -------------------- Security defaults --------------------
# Base values (can be overridden via env vars). When DEBUG=False we
# enforce stricter defaults below.
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    # In production prefer strict defaults; allow env override when needed
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)
    SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
    CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)

# -------------------- Cloudinary & storage --------------------
# Default storages (local). We'll enable Cloudinary only when packages and
# credentials are present.
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
# Use manifest storage only in production when collectstatic is run
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = config("MEDIA_URL", default="/media/")

# Cloudinary credentials (may be empty in local dev)

# Support CLOUDINARY_URL (format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME)
_cloudinary_url = config("CLOUDINARY_URL", default="")
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET", default="")

# If CLOUDINARY_URL is provided, parse it to fill credentials
if _cloudinary_url:
    try:
        parsed = urlparse(_cloudinary_url)
        # netloc is like 'API_KEY:API_SECRET@CLOUD_NAME'
        if parsed.scheme == "cloudinary":
            if parsed.username:
                CLOUDINARY_API_KEY = parsed.username
            if parsed.password:
                CLOUDINARY_API_SECRET = parsed.password
            if parsed.hostname:
                CLOUDINARY_CLOUD_NAME = parsed.hostname
    except Exception:
        logging.warning("Failed to parse CLOUDINARY_URL; falling back to individual CLOUDINARY_* vars")

# Enable Cloudinary only when running in production and packages + creds exist
CLOUDINARY_ENABLED = False
if not DEBUG and _package_available("cloudinary") and _package_available("cloudinary_storage"):
    if not (CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET):
        raise ImproperlyConfigured("Cloudinary packages installed but CLOUDINARY_URL or CLOUDINARY_* environment variables are missing in production")
    CLOUDINARY_ENABLED = True
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
else:
    MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
}


# -------------------- JWT config --------------------
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("JWT_ACCESS_MINUTES", default=60, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("JWT_REFRESH_DAYS", default=1, cast=int)),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# -------------------- Misc / app specific --------------------
UNIVERSITY_EMAIL_DOMAIN = config("UNIVERSITY_EMAIL_DOMAIN", default="ktu.edu")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

"""
Notes:
- Keep secrets out of VCS: use host environment or a protected `.env` file
  (not committed).
- On production, set: `DEBUG=False`, `SECRET_KEY`, `DATABASE_URL`,
  `CLOUDINARY_*` (if using Cloudinary), and proper `ALLOWED_HOSTS`.
- Run `python manage.py collectstatic --noinput` during deploy.
"""
