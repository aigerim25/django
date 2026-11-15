from settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

SQLITE_DB_NAME = 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, SQLITE_DB_NAME),
    }
}

INTERNAL_IPS = ['127.0.0.1']

SQL_LOG_ENABLED = config('BLOG_SQL_LOG', default=False, cast=bool)

if SQL_LOG_ENABLED:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {'class': 'logging.StreamHandler'},
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }