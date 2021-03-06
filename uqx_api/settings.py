"""
Django settings for uqx_api project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import courses
import datetime
import ldap
from django_auth_ldap.config import LDAPSearch
import django.contrib.staticfiles

try:
    import config
except ImportError:
    print "You do not have a config file, copy config.example.py to config.py"
    exit()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'uvgs)ive@a=l3$19x=2$w+s6qp@@qfjnk&pwhu_(kf+-sh@cl7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django_admin_bootstrapped.bootstrap3',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'provider',
    'provider.oauth2',
    'api',
    'rest_framework',
    'corsheaders',
)

if config.USE_LDAP:

    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

    AUTH_LDAP_SERVER_URI = config.LDAP_SERVER
    AUTH_LDAP_BIND_DN = config.LDAP_BIND_DN
    AUTH_LDAP_BIND_PASSWORD = config.LDAP_PASSWORD

    AUTH_LDAP_USER_SEARCH = LDAPSearch(config.LDAP_SEARCH_DN, 2, "(uid=%(user)s)")
    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "cn",
        "last_name": "cn",
        "email": "mail"
    }

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

REST_FRAMEWORK = {
    # specifying the renderers
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.OAuth2Authentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

JWT_AUTH = {
#    'JWT_ENCODE_HANDLER':
#    'rest_framework_jwt.utils.jwt_encode_handler',

#    'JWT_DECODE_HANDLER':
#    'rest_framework_jwt.utils.jwt_decode_handler',

#    'JWT_PAYLOAD_HANDLER':
#    'rest_framework_jwt.utils.jwt_payload_handler',

    #'JWT_SECRET_KEY': settings.SECRET_KEY,
#    'JWT_ALGORITHM': 'HS256',
#    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=24)
}

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    'api.context_processors.test_view',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

ROOT_URLCONF = 'uqx_api.urls'

WSGI_APPLICATION = 'uqx_api.wsgi.application'

CORS_ORIGIN_ALLOW_ALL = True

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CACHES = {
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    #     'LOCATION': 'uqx_api',
    #     'TIMEOUT': 60*60*24*14 #hold cache for 2 weeks
    # }
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 60*60*24*90  # hold cache for 3 months
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'api': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/api.log',
            'formatter': 'verbose'
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'api': {
            'handlers': ['api'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['django'],
            'propagate': True,
            'level': 'DEBUG',
        },
    },
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
#STATICFILES_DIRS = (
#    os.path.join(BASE_DIR, "static"),
#    '/var/www/static/',
#)
STATIC_ROOT = os.path.join(BASE_DIR, "api/static/")

DATABASES = {}

for name in courses.EDX_DATABASES:
    DATABASES[name] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': courses.EDX_DATABASES[name]['dbname'],
        'USER': config.SQL_USERNAME,
        'PASSWORD': config.SQL_PASSWORD,
        'HOST': config.SQL_HOST,
        'PORT': config.SQL_PORT,
    }

BRAND = 'AdelaideX'
BRAND_WEBSITE = 'https://www.adelaide.edu.au/adelaidex/'

YOUTUBE_CLIENT_ID = config.YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET = config.YOUTUBE_CLIENT_SECRET

TEMPLATE_DIRS = (
    BASE_DIR + '/apis'
    "%s/templates" % BASE_DIR
)