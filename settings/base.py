import os
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from settings.conf import *  # noqa


# ----------------------------------------------
# Path
#
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.asgi.application'

# ----------------------------------------------
# Apps
#
DJANGO_AND_THIRD_PARTY_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
PROJECT_APPS = [
    "apps.auths",
    "apps.blog",
]
INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

# ----------------------------------------------
# Middleware | Templates | Validators
#
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ----------------------------------------------
# Internationalization
#
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------------------------
# Static | Media
#
STATIC_URL = 'static/'
AUTH_USER_MODEL = 'auths.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Unfold admin
#
GITHUB_REPOSITORY_URL = config(  # noqa: F405
    'BLOG_GITHUB_URL', default='https://github.com/', cast=str,
)
UNFOLD_DOCS_URL = 'https://unfoldadmin.com/docs/'
POST_CHANGELIST_URL_NAME = 'admin:blog_post_changelist'
POST_STATUS_QUERY = '?status__exact={status}'
# Same values as Post.Status. Models can't be imported in settings.
POST_STATUS_PUBLISHED = 'published'
POST_STATUS_DRAFT = 'draft'


def post_list_link(status: str | None = None) -> str:
    """Link to the post list, optionally filtered by status (for TABS).

    `reverse_lazy("admin:blog_post_changelist") + '?...'` crashes on startup, so the link is
    built only when a page is rendered.
    """
    link = str(reverse_lazy(POST_CHANGELIST_URL_NAME))
    if status is None:
        return link
    return link + POST_STATUS_QUERY.format(status=status)


UNFOLD = {
    'SITE_TITLE': 'Blog API',
    'SITE_HEADER': 'Blog API',
    'SITE_SUBHEADER': 'Posts, comments and authors',
    'SITE_SYMBOL': 'article',
    'SITE_URL': '/admin/',
    'SITE_DROPDOWN': [
        {
            'icon': 'code',
            'title': _('GitHub repository'),
            'link': GITHUB_REPOSITORY_URL,
            'attrs': {'target': '_blank'},
        },
        {
            'icon': 'menu_book',
            'title': _('Unfold docs'),
            'link': UNFOLD_DOCS_URL,
            'attrs': {'target': '_blank'},
        },
    ],
    'ENVIRONMENT': 'apps.blog.callbacks.environment_callback',
    'DASHBOARD_CALLBACK': 'apps.blog.callbacks.dashboard_callback',
    'COLORS': {
        # Tailwind "teal" palette.
        'primary': {
            '50': 'oklch(98.4% 0.014 180.72)',
            '100': 'oklch(95.3% 0.051 180.801)',
            '200': 'oklch(91% 0.096 180.426)',
            '300': 'oklch(85.5% 0.138 181.071)',
            '400': 'oklch(77.7% 0.152 181.912)',
            '500': 'oklch(70.4% 0.14 182.503)',
            '600': 'oklch(60% 0.118 184.704)',
            '700': 'oklch(51.1% 0.096 186.391)',
            '800': 'oklch(43.7% 0.078 188.216)',
            '900': 'oklch(38.6% 0.063 188.416)',
            '950': 'oklch(27.7% 0.046 192.524)',
        },
    },
    'COMMAND': {
        'search_models': True,
        'show_history': True,
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': _('Overview'),
                'items': [
                    {
                        'title': _('Dashboard'),
                        'icon': 'dashboard',
                        'link': reverse_lazy('admin:index'),
                    },
                ],
            },
            {
                'title': _('Content'),
                'separator': True,
                'items': [
                    {
                        'title': _('Posts'),
                        'icon': 'article',
                        'link': reverse_lazy('admin:blog_post_changelist'),
                        'badge': 'apps.blog.callbacks.drafts_badge',
                    },
                    {
                        'title': _('Comments'),
                        'icon': 'chat',
                        'link': reverse_lazy('admin:blog_comment_changelist'),
                    },
                    {
                        'title': _('Categories'),
                        'icon': 'category',
                        'link': reverse_lazy('admin:blog_category_changelist'),
                    },
                    {
                        'title': _('Tags'),
                        'icon': 'sell',
                        'link': reverse_lazy('admin:blog_tag_changelist'),
                    },
                ],
            },
            {
                'title': _('Users & Access'),
                'separator': True,
                'items': [
                    {
                        'title': _('Users'),
                        'icon': 'person',
                        'link': reverse_lazy('admin:auths_user_changelist'),
                        'permission': 'apps.blog.callbacks.is_superuser',
                    },
                    {
                        'title': _('Groups'),
                        'icon': 'group',
                        'link': reverse_lazy('admin:auth_group_changelist'),
                        'permission': 'apps.blog.callbacks.is_superuser',
                    },
                ],
            },
        ],
    },
    'TABS': [
        {
            'models': ['blog.post'],
            'items': [
                {
                    'title': _('All'),
                    'link': lambda request: post_list_link(),
                },
                {
                    'title': _('Published'),
                    'link': lambda request: post_list_link(POST_STATUS_PUBLISHED),
                },
                {
                    'title': _('Drafts'),
                    'link': lambda request: post_list_link(POST_STATUS_DRAFT),
                },
            ],
        },
    ],
}
