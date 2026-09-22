"""
Django settings for AI Document Intelligence Platform.
"""

import os
from pathlib import Path
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project apps
    'accounts',
    'landing',
    'dashboard',
    'documents',
    'ai_core',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'doc_intelligence.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'doc_intelligence.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'landing:home'

# Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Security settings
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Email Configuration (SMTP)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend').strip("'\"")
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com').strip("'\"")
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='').strip("'\"")
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='').strip("'\"")
raw_from_email = config('DEFAULT_FROM_EMAIL', default='').strip("'\"")

if raw_from_email and 'docintel.com' not in raw_from_email:
    DEFAULT_FROM_EMAIL = raw_from_email
elif EMAIL_HOST_USER:
    DEFAULT_FROM_EMAIL = f"DocIntel <{EMAIL_HOST_USER}>"
else:
    DEFAULT_FROM_EMAIL = 'DocIntel <noreply@docintel.com>'

# Fallback to console backend if EMAIL_HOST_USER is not configured (allows seamless local testing)
if not EMAIL_HOST_USER and EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# AI Configuration
AI_PROVIDER = config('AI_PROVIDER', default='groq')

# Groq Configuration
GROQ_API_KEY = config('GROQ_API_KEY', default='')
GROQ_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')

# Ollama Configuration
OLLAMA_URL = config('OLLAMA_URL', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3')

# FAISS index storage
FAISS_INDEX_DIR = BASE_DIR / 'media' / 'faiss_indexes'
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
os.makedirs(BASE_DIR / 'media' / 'documents', exist_ok=True)
os.makedirs(BASE_DIR / 'media' / 'avatars', exist_ok=True)
