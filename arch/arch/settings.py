
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


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-@y5fcxi+h*vakr5366gli%1(i(&@_xd%(3%w-cx)*l2srj+k_-'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '@y5fcxi+h*vakr5366gli%1(i(&@_xd%(3%w-cx)*l2srj+k_-')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# AI configuration
ACTIVATE_AI_SEARCH = True       # uses torch==2.0.0 sentence-transformers==2.2.2
QUANTIZE_CLIP_MODELS = False     # quantize the model used by the search module.
ACTIVATE_FACE_DETECTION = True  # uses Tensorflow and cvlib==0.2.7

# Moderation settings
HIDE_COMMENTS = False           # hides new comments as default until they are approved by a moderator


ALLOWED_HOSTS = []              # ['example.de']
CSRF_TRUSTED_ORIGINS = []       # ['https://example.de']

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Application definition

INSTALLED_APPS = [

    # 'django_extensions',                # needed in order to use graph_models

    # default apps:
    'django.contrib.admin',
    'django.contrib.auth',              # Core authentication framework and its default models.
    'django.contrib.contenttypes',      # Django content type system (allows permissions to be associated with models).
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # custom apps:
    'mathfilters',
    'guardian',                         # Django object-level permissions
    'django_q',                         # Django Q Cluster
    'arch_app.apps.ArchAppConfig',      # main app
    # 'languages',                      # not used currently
    # 'debug_toolbar',                  # debug toolbar
    'bootstrap5',
    "crispy_forms",
    "crispy_bootstrap5",

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Manages sessions across requests
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Associates users with requests using sessions.
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
    'guardian.backends.ObjectPermissionBackend',
)


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
# }

DATABASES = {

            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                 'NAME': 'arch_db',
                 'USER': 'db_admin',
                 'PASSWORD': 'arch',
                 'HOST': 'localhost',
                 'PORT': '',
                'TEST': {
                    'NAME': 'arch_db_test',
                },
            }
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-cache-arch',
#     }
# }

# Django Q settings (using Django’s database backend as a message broker)
# Documentation: https://django-q2.readthedocs.io/en/master/configure.html
Q_CLUSTER = {
    'sync': False,      # set to True to run synchronous, good for debugging, default is False
    'name': 'ARCH',
    'workers': 4,
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

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-gb'
# LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

# USE_L10N = True

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
# LOGOUT_REDIRECT_URL = "/"

# directory where the archive will be created
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
# MEDIA_URL = '/arch_app/static/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'arch_app/static')

# path to the translations
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'), )

# settings for graph_models
GRAPH_MODELS = {
    'all_applications': False,
    'group_models': True,
    'app_labels': ["arch_app"],
}

MAX_FILE_SIZE = 2621440 * 100  # i.e. 2.5 MB * 100

LANGUAGES = [
    ('de', _('German')),
    ('en-gb', _('English')),
]

CONTACT_EMAIL = 'admin@example.com'

# ToDo integrate email support ( https://docs.djangoproject.com/en/4.0/topics/email/ )
# logs any emails sent to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@virtuos.uni-osnabrueck.de'
#EMAIL_USE_TLS = True
#EMAIL_HOST = 'relay.uni-osnabrueck.de' --> server
# EMAIL_HOST_USER = 'youremail@gmail.com'
# EMAIL_HOST_PASSWORD = 'yourpassword'
#EMAIL_PORT = 25 --> server



# Used by debug toolbar
INTERNAL_IPS = [

    "127.0.0.1",

]

# Logger
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
