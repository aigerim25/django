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

# INSTALLED_APPS += [
#     'debug_toolbar',
# ]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1']
