"""Django settings for sami_project."""

import mimetypes
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in {
    "1", "true", "yes", "on"
}

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY and DEBUG:
    SECRET_KEY = "django-insecure-local-development-key"
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "La variable de entorno DJANGO_SECRET_KEY es obligatoria."
    )

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False").lower() in {
    "1", "true", "yes", "on"
}
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "False").lower() in {
    "1", "true", "yes", "on"
}
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE", "False").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

ALLOWED_HOSTS = [
    "samitravelstours.com",
    "www.samitravelstours.com",
    "samitravelsytours.jaimeberrios.com",
    "localhost",
    "127.0.0.1",
]

# Caddy termina HTTPS y reenvía la petición a Gunicorn por la red interna.
# Esta configuración es segura mientras Gunicorn no esté expuesto directamente
# a Internet y Caddy reemplace (no concatene) X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

CSRF_TRUSTED_ORIGINS = [
    'https://samitravelstours.com',
    'https://www.samitravelstours.com',
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tailwind",
    "theme",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "core",
    "sami_admin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sami_project.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "sami_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sami_project.wsgi.application"
ASGI_APPLICATION = "sami_project.asgi.application"

DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").lower()
if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DB_ENGINE == "mysql":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE"),
        "USER": os.environ.get("MYSQL_USER"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": os.environ.get("MYSQL_HOST"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "CONN_MAX_AGE": int(os.environ.get("MYSQL_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }}
    required_database_settings = {
        "MYSQL_DATABASE": DATABASES["default"]["NAME"],
        "MYSQL_USER": DATABASES["default"]["USER"],
        "MYSQL_PASSWORD": DATABASES["default"]["PASSWORD"],
        "MYSQL_HOST": DATABASES["default"]["HOST"],
    }
    missing_database_settings = [
        key for key, value in required_database_settings.items() if not value
    ]
    if missing_database_settings:
        raise ImproperlyConfigured(
            "Faltan variables de entorno obligatorias para MySQL: "
            + ", ".join(missing_database_settings)
        )
else:
    raise ImproperlyConfigured("DB_ENGINE debe ser 'mysql' o 'sqlite'.")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = os.environ.get("ACCOUNT_EMAIL_VERIFICATION", "none")
LOGIN_URL = "/sami-admin/login/"
LOGIN_REDIRECT_URL = "sami_admin:dashboard"
LOGOUT_REDIRECT_URL = "/"

CONTACT_EMAIL = os.environ.get(
    "CONTACT_EMAIL",
    "contacto@samitravelstours.com",
)
PUBLIC_FORM_RATE_LIMIT = int(os.environ.get("PUBLIC_FORM_RATE_LIMIT", "5"))
PUBLIC_FORM_RATE_WINDOW = int(os.environ.get("PUBLIC_FORM_RATE_WINDOW", "3600"))
ADMIN_LOGIN_RATE_LIMIT = int(os.environ.get("ADMIN_LOGIN_RATE_LIMIT", "5"))
ADMIN_LOGIN_RATE_WINDOW = int(os.environ.get("ADMIN_LOGIN_RATE_WINDOW", "900"))

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    }
}

# No configure Google simultáneamente aquí y mediante SocialApp en /admin/.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS["google"]["APPS"] = [
        {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
        }
    ]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/El_Salvador"
USE_I18N = True
USE_TZ = True

# Caddy conserva un manejador heredado para /static/ con un volumen separado.
# /assets/ pasa por el proxy hacia Django y permite que WhiteNoise sirva el
# mismo manifiesto versionado que genera collectstatic dentro de la imagen.
STATIC_URL = "/assets/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Garantiza tipos MIME correctos incluso en imágenes Linux mínimas que no
# incluyen una base de datos completa de tipos del sistema.
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)

# collectstatic genera nombres versionados y archivos .gz/.br. WhiteNoise los
# sirve directamente cuando Caddy solo actua como proxy hacia Gunicorn.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = os.environ.get(
    "NPM_BIN_PATH",
    r"C:\Program Files\nodejs\npm.cmd" if os.name == "nt" else "npm",
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
