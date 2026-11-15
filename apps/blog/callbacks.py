import json
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpRequest
from django.urls import reverse

from apps.blog.models import Category, Comment, Post

PRODUCTION_ENV_ID = 'prod'
ENVIRONMENT_LOCAL = ['Local', 'warning']
ENVIRONMENT_PRODUCTION = ['Production', 'danger']
TOP_AUTHORS_LIMIT = 5
PERCENT = 100

User = get_user_model()


def environment_callback(request: HttpRequest) -> list[str]:
    """Badge in the header: orange "Local" or red "Production"."""
    if settings.ENV_ID == PRODUCTION_ENV_ID:
        return ENVIRONMENT_PRODUCTION
    return ENVIRONMENT_LOCAL


def drafts_badge(request: HttpRequest) -> int:
    """Number of drafts, shown next to "Posts" in the sidebar."""
    return Post.objects.filter(status=Post.Status.DRAFT).count()


def is_superuser(request: HttpRequest) -> bool:
    """Sidebar permission: only superusers see "Users & Access"."""
    return request.user.is_superuser


def _percent(part: int, total: int) -> int:
    if total == 0:
        return 0
    return round(part * PERCENT / total)


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Data for the admin home page (templates/admin/index.html)."""
    post_stats = Post.objects.aggregate(
        total=Count('id'),
        published=Count('id', filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count('id', filter=Q(status=Post.Status.DRAFT)),
    )

    categories = Category.objects.annotate(
        post_count=Count('post'),
    ).order_by('-post_count', 'name')
    chart_data = {
        'labels': [category.name for category in categories],
        'datasets': [
            {
                'label': 'Posts',
                'data': [category.post_count for category in categories],
            },
        ],
    }

    top_authors = (
        User.objects
        .annotate(post_count=Count('post'))
        .filter(post_count__gt=0)
        .order_by('-post_count', 'email')[:TOP_AUTHORS_LIMIT]
    )
    authors_table = {
        'headers': ['Author', 'Email', 'Posts'],
        'rows': [
            [author.get_full_name(), author.email, author.post_count]
            for author in top_authors
        ],
    }

    context.update(
        {
            'cards': [
                {
                    'title': 'Users',
                    'value': User.objects.count(),
                    'icon': 'person',
                    'link': reverse('admin:auths_user_changelist'),
                },
                {
                    'title': 'Published posts',
                    'value': post_stats['published'],
                    'icon': 'task_alt',
                    'link': reverse('admin:blog_post_changelist')
                    + f'?status__exact={Post.Status.PUBLISHED}',
                },
                {
                    'title': 'Drafts',
                    'value': post_stats['drafts'],
                    'icon': 'edit_note',
                    'link': reverse('admin:blog_post_changelist')
                    + f'?status__exact={Post.Status.DRAFT}',
                },
                {
                    'title': 'Comments',
                    'value': Comment.objects.count(),
                    'icon': 'chat',
                    'link': reverse('admin:blog_comment_changelist'),
                },
            ],
            'chart_data': json.dumps(chart_data),
            'authors_table': authors_table,
            'progress': [
                {
                    'title': 'Published',
                    'count': post_stats['published'],
                    'value': _percent(post_stats['published'], post_stats['total']),
                },
                {
                    'title': 'Drafts',
                    'count': post_stats['drafts'],
                    'value': _percent(post_stats['drafts'], post_stats['total']),
                },
            ],
        }
    )
    return context
