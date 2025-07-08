from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# ────────────────────────────────────────────────────────────────
# Proje kökü & .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")                 # .env dosyan yoksa atla

# ─── Güvenlik
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "<change-this>")
DEBUG      = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h] or ["*"]

# ─── Uygulamalar
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local
    "users",
    "api",
]

# ─── Middleware  (CORS → Common'dan önce)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ─── Templates  (admin için zorunlu)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # klasör yoksa sorun değil
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

WSGI_APPLICATION = "config.wsgi.application"

# ─── Veritabanı  (Heroku varsa DATABASE_URL otomatik gelir)
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )
}

# ─── Auth & DRF
AUTH_USER_MODEL = "users.User"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# ─── Şifre kuralları (varsayılan)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Uluslararası
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ   = True

# ─── Statik dosyalar / Vite build
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []   
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─── CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",      # Vite dev
    "exp://127.0.0.1:8081",       # Expo dev
]

# ─── Diğer
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")