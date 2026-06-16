import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'health-analytics-secure-key-2024')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts',
    'core',
    'etl',
    'analytics',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'health_analytics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'health_analytics.wsgi.application'

import dj_database_url

_db_url = os.getenv('DATABASE_URL', '') or os.getenv('POSTGRES_URL_NON_POOLING', '')
if not _db_url:
    _pguser = os.getenv('PGUSER') or os.getenv('POSTGRES_USER') or ''
    _pgpass = os.getenv('PGPASSWORD') or os.getenv('POSTGRES_PASSWORD') or ''
    _pghost = os.getenv('PGHOST') or os.getenv('POSTGRES_HOST') or ''
    _pgdb = os.getenv('PGDATABASE') or os.getenv('POSTGRES_DATABASE') or ''
    _pgport = os.getenv('PGPORT', '5432')
    if _pguser and _pgpass and _pghost and _pgdb:
        _db_url = f'postgres://{_pguser}:{_pgpass}@{_pghost}:{_pgport}/{_pgdb}'
if _db_url:
    DATABASES = {'default': dj_database_url.config(default=_db_url, conn_max_age=60)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = '/login/'

# Brevo (Sendinblue) config
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
BREVO_SMTP_USER = os.getenv('BREVO_SMTP_USER', '')
if not BREVO_API_KEY:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
MEDIA_URL = '/api/media/'
MEDIA_ROOT = '/tmp/analitica-media' if os.getenv('VERCEL') else os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'accounts.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
