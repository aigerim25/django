import random
import time
from typing import Any

from faker import Faker

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()

# Defaults for the arguments
DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

# Users
SEED_PASSWORD = 'seedpass123'
EMAIL_DOMAINS = ['example.com', 'mail.com', 'blog.dev']
INACTIVE_USERS_SHARE = 0.15
STAFF_USERS_SHARE = 0.1
COMMENTING_USERS_SHARE = 0.8
MIN_SPECIAL_USERS = 1

# Categories and tags
CATEGORY_NAMES = [
    'Python',
    'Django',
    'DevOps',
    'Databases',
    'Frontend',
    'Testing',
    'Career',
    'Security',
]
TAG_NAMES = [
    'beginner',
    'advanced',
    'tutorial',
    'tips',
    'orm',
    'rest-api',
    'postgresql',
    'docker',
    'linux',
    'git',
    'performance',
    'async',
    'celery',
    'redis',
    'javascript',
    'react',
    'css',
    'pytest',
    'interview',
    'best-practices',
]
TITLE_WORDS = [
    'django', 'python', 'orm', 'query', 'model', 'view', 'cache', 'deploy',
    'docker', 'server', 'database', 'index', 'migration', 'test', 'api',
    'admin', 'form', 'template', 'signal', 'middleware', 'async', 'task',
    'guide', 'tricks', 'mistakes', 'patterns', 'basics', 'deep', 'fast',
    'simple', 'modern', 'practical', 'clean', 'secure', 'scaling', 'debugging',
]
MIN_TITLE_WORDS = 3
MAX_TITLE_WORDS = 7
MIN_PARAGRAPHS = 3
MAX_PARAGRAPHS = 6
PARAGRAPH_SEPARATOR = '\n\n'
PUBLISHED_SHARE = 0.7
NO_CATEGORY_SHARE = 0.1
MIN_TAGS = 0
MAX_TAGS = 5
SLUG_SUFFIX_START = 2
# Room for "-<number>" at the end of a long slug.
SLUG_SUFFIX_RESERVE = 6

# Comments
#
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
SUMMARY_LABEL_WIDTH = 11
SUMMARY_NUMBER_WIDTH = 5

class Command(BaseCommand):
    help = 'Fill the database with fake data.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--users', type=int, default=DEFAULT_USERS,
            help='Number of users to create',
        )
        parser.add_argument(
            '--posts', type=int, default=DEFAULT_POSTS,
            help='Number of posts to create',
        )
        parser.add_argument(
            '--comments', type=int, default=DEFAULT_COMMENTS,
            help='Number of comments to create',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete existing data before seeding',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        users_count: int = options['users']
        posts_count: int = options['posts']
        comments_count: int = options['comments']
        clear: bool = options['clear']

        for name in ('users', 'posts', 'comments'):
            if options[name] < 0:
                raise CommandError(f'--{name} must not be negative.')

        self.fake = Faker()
        started_at = time.perf_counter()

        # One transaction: if a CommandError is raised in the middle,
        # nothing is saved.
        with transaction.atomic():
            if clear:
                self.clear_data()

            users = self.create_users(users_count)
            categories = self.create_categories()
            tags = self.create_tags()
            posts = self.create_posts(posts_count)
            comments = self.create_comments(comments_count, posts)

        elapsed = time.perf_counter() - started_at
        self.write_summary(
            {
                'Users': len(users),
                'Categories': len(categories),
                'Tags': len(tags),
                'Posts': len(posts),
                'Comments': len(comments),
            },
            elapsed,
        )
    # Clear
    #
    def clear_data(self) -> None:
        """Delete everything except superusers."""
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING('Old data deleted.'))

    # Users
    #
    def create_users(self, count: int) -> list[User]:
        used_emails = set(User.objects.values_list('email', flat=True))
        # Hashing is slow on purpose, so it is done only once.
        password_hash = make_password(SEED_PASSWORD)

        users = []
        for _ in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            users.append(
                User(
                    email=self.unique_email(first_name, last_name, used_emails),
                    first_name=first_name,
                    last_name=last_name,
                    password=password_hash,
                )
            )

        # Pick inactive and staff users. They don't overlap,
        # so every staff user is active.
        shuffled = random.sample(users, len(users))
        inactive_count = self.share_count(len(users), INACTIVE_USERS_SHARE)
        staff_count = self.share_count(len(users), STAFF_USERS_SHARE)
        for user in shuffled[:inactive_count]:
            user.is_active = False
        for user in shuffled[inactive_count:inactive_count + staff_count]:
            user.is_staff = True

        return User.objects.bulk_create(users)

    @staticmethod
    def share_count(total: int, share: float) -> int:
        """How many objects get a property: at least 1 if there are any objects."""
        if total == 0:
            return 0
        return max(MIN_SPECIAL_USERS, round(total * share))

    @staticmethod
    def unique_email(first_name: str, last_name: str, used_emails: set[str]) -> str:
        local_part = f'{slugify(first_name)}.{slugify(last_name)}'.replace('-', '')
        domain = random.choice(EMAIL_DOMAINS)
        email = f'{local_part}@{domain}'
        number = SLUG_SUFFIX_START
        while email in used_emails:
            email = f'{local_part}{number}@{domain}'
            number += 1
        used_emails.add(email)
        return email

    # Categories and tags
    #
    def create_categories(self) -> list[Category]:
        existing = set(Category.objects.values_list('slug', flat=True))
        new = [
            Category(name=name, slug=slugify(name))
            for name in CATEGORY_NAMES
            if slugify(name) not in existing
        ]
        return Category.objects.bulk_create(new)

    def create_tags(self) -> list[Tag]:
        existing = set(Tag.objects.values_list('slug', flat=True))
        new = [
            Tag(name=name, slug=slugify(name))
            for name in TAG_NAMES
            if slugify(name) not in existing
        ]
        return Tag.objects.bulk_create(new)    

    # Posts
    #
    def create_posts(self, count: int) -> list[Post]:
        if count == 0:
            return []

        authors = list(User.objects.all())
        if not authors:
            raise CommandError('Cannot create posts: there are no users. Use --users.')

        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        used_slugs = set(Post.objects.values_list('slug', flat=True))
        slug_max_length = Post._meta.get_field('slug').max_length

        posts = []
        for _ in range(count):
            title = self.fake.sentence(
                nb_words=random.randint(MIN_TITLE_WORDS, MAX_TITLE_WORDS),
                ext_word_list=TITLE_WORDS,
            ).rstrip('.')
            paragraphs = self.fake.paragraphs(
                nb=random.randint(MIN_PARAGRAPHS, MAX_PARAGRAPHS),
            )
            is_published = random.random() < PUBLISHED_SHARE
            has_category = bool(categories) and random.random() >= NO_CATEGORY_SHARE
            posts.append(
                Post(
                    author=random.choice(authors),
                    title=title,
                    # bulk_create does not call save(), so the slug is set here.
                    slug=self.unique_slug(title, used_slugs, slug_max_length),
                    body=PARAGRAPH_SEPARATOR.join(paragraphs),
                    category=random.choice(categories) if has_category else None,
                    status=Post.Status.PUBLISHED if is_published else Post.Status.DRAFT,
                )
            )

        posts = Post.objects.bulk_create(posts)

        # After bulk_create the posts have ids, so tags can be set.
        for post in posts:
            tags_count = random.randint(MIN_TAGS, min(MAX_TAGS, len(tags)))
            post.tags.set(random.sample(tags, tags_count))

        return posts

    @staticmethod
    def unique_slug(title: str, used_slugs: set[str], max_length: int) -> str:
        base = slugify(title)[:max_length - SLUG_SUFFIX_RESERVE].strip('-')
        slug = base
        number = SLUG_SUFFIX_START
        while slug in used_slugs:
            slug = f'{base}-{number}'
            number += 1
        used_slugs.add(slug)
        return slug

    # Comments
    #
    def create_comments(self, count: int, new_posts: list[Post]) -> list[Comment]:
        if count == 0:
            return []

        users = list(User.objects.all())
        if not users:
            raise CommandError('Cannot create comments: there are no users. Use --users.')

        # Published posts: the old ones from the database + the new ones
        # that are already in memory.
        new_ids = {post.pk for post in new_posts}
        published_posts = [
            post for post in new_posts if post.status == Post.Status.PUBLISHED
        ] + list(
            Post.objects.filter(status=Post.Status.PUBLISHED).exclude(pk__in=new_ids)
        )
        if not published_posts:
            raise CommandError(
                'Cannot create comments: there are no published posts. Use --posts.'
            )

        commenters_count = max(
            MIN_SPECIAL_USERS, round(len(users) * COMMENTING_USERS_SHARE),
        )
        commenters = random.sample(users, commenters_count)

        comments = [
            Comment(
                post=random.choice(published_posts),
                author=random.choice(commenters),
                body=self.fake.paragraph(
                    nb_sentences=random.randint(
                        MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES,
                    ),
                    variable_nb_sentences=False,
                ),
            )
            for _ in range(count)
        ]
        return Comment.objects.bulk_create(comments)

    # Summary
    #
    def write_summary(self, counts: dict[str, int], elapsed: float) -> None:
        for label, number in counts.items():
            self.stdout.write(
                f'{label + ":":<{SUMMARY_LABEL_WIDTH}}'
                f'{number:>{SUMMARY_NUMBER_WIDTH}} created'
            )
        self.stdout.write(self.style.SUCCESS(f'Done in {elapsed:.2f} seconds'))

        