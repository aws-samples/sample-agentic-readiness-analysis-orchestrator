# Django settings for helpdesk project.
# Django 1.4 / Python 2.7. Created 2012, last edited 2018.
import os

DEBUG = True            # left on in production - leaks tracebacks
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('IT Ops', 'it-ops@acme-corp.internal'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'helpdesk',
        'USER': 'helpdesk',
        'PASSWORD': 'helpdesk2012',     # plaintext db password
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'

# Secret key committed to source control
SECRET_KEY = 'x9d2#kf!3v_legacy_secret_do_not_change_2012'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'helpdesk.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'tickets',
)

EMAIL_HOST = 'exchange.acme-corp.internal'
EMAIL_PORT = 25
