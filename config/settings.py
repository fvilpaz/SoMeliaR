import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-demo-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)

# --- CLOUDINARY CONFIG ---
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "")

INSTALLED_APPS = [
    # 1. Cloudinary Storage SIEMPRE primero para capturar los archivos
    "cloudinary_storage",
    "cloudinary",
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Apps propias
    "core",
    "bodega",
    "proveedores",
    "pedidos",
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.app_config",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- BASE DE DATOS ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = "es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS (CSS, JS) ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# --- ARCHIVOS MULTIMEDIA (FOTOS DE PERFIL) ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if CLOUDINARY_URL:
    # Si detecta la clave en Render, usa Cloudinary
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- RUTAS DE LOGIN ---
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"

# --- IA Y OTROS ---
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"