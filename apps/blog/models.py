from django.db import models
from django.conf import settings
from django.db.models import CharField,SlugField,BooleanField,TextField,DateTimeField,ForeignKey,ManyToManyField,CASCADE,SET_NULL,Model, TextChoices

CATEGORY_NAME_MAX_LENGTH = 100
TAG_NAME_MAX_LENGTH = 50
POST_TITLE_MAX_LENGTH = 200
POST_SLUG_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 20

class Category(Model):
    name = CharField(
        max_length = CATEGORY_NAME_MAX_LENGTH,
        unique = True,
    )
    slug = SlugField(
        unique = True,
    )

class Tag(Model):
    name = CharField(
        max_length = TAG_NAME_MAX_LENGTH,
        unique = True,
    )
    slug = SlugField(
        unique = True,
    )

class Post(Model):
    class Status(TextChoices):
            DRAFT = 'draft', 'Draft'
            PUBLISHED = 'published', 'Published'
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
    )
    title = CharField(
        max_length = POST_TITLE_MAX_LENGTH,
    )
    slug = SlugField(
        unique = True,
    )
    body = TextField(
        max_length = 100,
    )
    category = ForeignKey(
        to=Category, 
        on_delete=SET_NULL,
        null=True,
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True,
        related_name='posts',
    )
    status = CharField(
        max_length = STATUS_MAX_LENGTH,
        choices = Status.choices,
        default = Status.DRAFT,
    )
    created_at = DateTimeField(
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        auto_now=True,
    )

class Comment(Model):
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
    )
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
    )
    body = TextField(
        max_length = 100,
    )
    created_at = DateTimeField(
        auto_now_add=True,
    )


