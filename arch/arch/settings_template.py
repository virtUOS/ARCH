
"""
Django settings for arch project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path
import django
from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '@y5fcxi+h*vakr5366gli%1(i(&@_xd%(3%w-cx)*l2srj+k_-')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ARCH App Configuration
CONTACT_EMAIL = 'admin@example.com'
ACTIVATE_AI_SEARCH = True       # Enables searching for images (requires torch==2.0.0 and sentence-transformers==2.2.2)
QUANTIZE_CLIP_MODELS = True     # Quantize the AI models used by the search module to reduce memory usage
ACTIVATE_FACE_DETECTION = True  # Automatically detects faces on uploaded images (requires Tensorflow and cvlib==0.2.7)
HIDE_COMMENTS = False           # Hides new comments as default until they are approved by a moderator
MAX_FILE_SIZE = 2621440 * 100   # Maximum file size for uploads in bytes (i.e. 2.5 MB * 100)

# General Django settings
ALLOWED_HOSTS = ['example.de']
CSRF_TRUSTED_ORIGINS = ['https://example.de']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# settings for graph_models (for developers)
# GRAPH_MODELS = {
#     'all_applications': False,
#     'group_models': True,
#     'app_labels': ["arch_app"],
# }

INSTALLED_APPS = [
    # 'django_extensions',              # needed in order to use graph_models (for developers)
    'django.contrib.admin',
    'django.contrib.auth',              # Core authentication framework and its default models.
    'django.contrib.contenttypes',      # Django content type system (allows permissions to be associated with models).
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # custom apps:
    'mathfilters',                      # math filters for Django templates
    'guardian',                         # Django object-level permissions
    'django_q',                         # Django Q Cluster
    'arch_app.apps.ArchAppConfig',      # main ARCH app
    'bootstrap5',                       # bootstrap5 django template integration
    "crispy_forms",                     # crispy forms
    "crispy_bootstrap5",                # crispy forms for bootstrap5
    # 'debug_toolbar',                  # debug toolbar (for developers)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'arch.urls'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
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

WSGI_APPLICATION = 'arch.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'guardian.backends.ObjectPermissionBackend',  # Django object-level permissions (Django Guardian)
)

# Database settings (PostgreSQL required)
DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                 'NAME': 'arch_db',   # name of the database, replace with your database name
                 'USER': 'db_admin',  # username to connect to the database
                 'PASSWORD': 'arch',  # password to connect to the database
                 'HOST': 'localhost',
                 'PORT': '',
                'TEST': {
                    'NAME': 'arch_db_test',
                },
            }
}

# Django Q settings (using Django’s database backend as a message broker)
# Documentation: https://django-q2.readthedocs.io/en/master/configure.html
Q_CLUSTER = {
    'sync': False,      # set to True to run synchronous, good for debugging, default is False
    'name': 'ARCH',     # name of the cluster
    'workers': 4,       # number of worker processes, adapt to your needs
    'recycle': 500,     # number of tasks a worker can process before recycling, default 500
    'timeout': 30,      # seconds a worker is allowed to spend on a task, default is None (unlimited)
    'max_attempts': 5,  # maximum number of attempts a task will be tried before it fails, default 0 (no limit)
    'retry': 90,        # seconds to wait before retrying failed tasks, default 60 (should be more than timeout)
    'save_limit': 250,  # number of successful tasks to keep in the database, default 250
    'queue_limit': 50,  # how many tasks are kept in memory by a single cluster, default worker count * 2
    'label': 'Tasks',   # label for Admin UI, default is 'Django Q2'
    'bulk': 5,          # number of messages send to the cluster at once, default 1
    'orm': 'default'    # name of the database connection to use for ORM models, default 'default'
}

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-gb'         # default language (e.g. change to 'de' for German)
TIME_ZONE = 'Europe/Berlin'     # default time zone, change to your time zone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_DIRS = []

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# auth user
AUTH_USER_MODEL = 'arch_app.User'

LOGIN_REDIRECT_URL = "/"

# Media url and directory (where the uploaded media files will be stored)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# path to the translations
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )

LANGUAGES = [
    ('de', _('German')),
    ('en-gb', _('English')),
]

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'    # development only to print emails to the console
DEFAULT_FROM_EMAIL = 'no-reply@arch.de'                             # default sender email
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = 'youremail@gmail.com'
# EMAIL_HOST_PASSWORD = 'yourpassword'
# EMAIL_PORT = 25  # port for the mail server

# Used by debug toolbar (for developers)
INTERNAL_IPS = [
    "127.0.0.1",
]

# Logger settings
LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs', 'logs.log')
LOG_FOLDER_PATH = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_FOLDER_PATH):
    os.makedirs(LOG_FOLDER_PATH)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ' [%(levelname)s] %(filename)s %(funcName)s  %(lineno)d: %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(filename)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'ARCH_console_logger': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'ARCH_file_logger': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
