from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from django.contrib import admin
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Category, Comment, Post, Tag

COMMENT_BODY_PREVIEW_LENGTH = 60
COMMENTS_INLINE_PER_PAGE = 10
SECTION_HEIGHT = 300
STATUS_LABELS = {
    Post.Status.PUBLISHED: 'success',
    Post.Status.DRAFT: 'warning',
}
CHANGE_PERMISSION = 'change'


# ----------------------------------------------
# Category and Tag
#
class CategoryPostsSection(TableSection):
    """Expandable row in the category list: the posts of this category."""

    verbose_name = _('Posts of this category')
    related_name = 'post_set'
    fields = ('title', 'status', 'created_at')
    height = SECTION_HEIGHT


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        # One query for the counts + one prefetch for the expandable rows.
        return (
            super().get_queryset(request)
            .annotate(post_count=Count('post'))
            .prefetch_related('post_set')
        )

    @display(description=_('Posts'), ordering='post_count')
    def post_count(self, obj: Category) -> int:
        return obj.post_count


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(post_count=Count('posts'))

    @display(description=_('Posts'), ordering='post_count')
    def post_count(self, obj: Tag) -> int:
        return obj.post_count


# ----------------------------------------------
# Comment
#
@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('post_title', 'author', 'short_body', 'created_at')
    list_filter = (
        ('post', AutocompleteSelectFilter),
        ('author', AutocompleteSelectFilter),
        ('created_at', RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ('body', 'author__email', 'post__title')
    autocomplete_fields = ('post', 'author')
    list_select_related = ('post', 'author')

    @display(description=_('Post'), ordering='post__title')
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description=_('Body'))
    def short_body(self, obj: Comment) -> str:
        return Truncator(obj.body).chars(COMMENT_BODY_PREVIEW_LENGTH)


# ----------------------------------------------
# Post
#
class CommentInline(TabularInline):
    model = Comment
    fields = ('author', 'body', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)
    extra = 0
    tab = True
    per_page = COMMENTS_INLINE_PER_PAGE

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        return (
            super().get_queryset(request)
            .select_related('author')
            .order_by('-created_at')
        )


class PostCommentsSection(TableSection):
    """Expandable row in the post list: the comments of this post."""

    verbose_name = _('Comments')
    related_name = 'comment_set'
    fields = ('author', 'short_body', 'created_at')
    height = SECTION_HEIGHT

    def short_body(self, obj: Comment) -> str:
        return Truncator(obj.body).chars(COMMENT_BODY_PREVIEW_LENGTH)

    short_body.short_description = _('Body')


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        'post_header',
        'status_label',
        'category',
        'tags_dropdown',
        'comment_count',
        'created_at',
    )
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('category', RelatedDropdownFilter),
        ('tags', MultipleRelatedDropdownFilter),
        ('author', AutocompleteSelectFilter),
        ('created_at', RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ('title', 'body', 'author__email')
    list_sections = (PostCommentsSection,)

    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('author', 'category', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    formfield_overrides = {
        TextField: {'widget': WysiwygWidget},
    }
    warn_unsaved_form = True
    inlines = (CommentInline,)
    fieldsets = (
        (_('Content'), {
            'classes': ['tab'],
            'fields': ('title', 'slug', 'body'),
        }),
        (_('Classification'), {
            'classes': ['tab'],
            'fields': ('category', 'tags', 'status'),
        }),
        (_('Meta'), {
            'classes': ['tab'],
            'fields': ('author', 'created_at', 'updated_at'),
        }),
    )

    actions = ('publish_selected', 'move_to_drafts')
    actions_row = ('toggle_status',)
    actions_list = ('publish_all_drafts',)
    actions_detail = ('open_comments',)
    actions_submit_line = ('save_and_publish',)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        # No N+1: author and category come with a JOIN,
        # tags and comments come with one extra query each.
        return (
            super().get_queryset(request)
            .select_related('author', 'category')
            .prefetch_related(
                'tags',
                Prefetch(
                    'comment_set',
                    queryset=Comment.objects.select_related('author'),
                ),
            )
            .annotate(comment_count=Count('comment'))
        )

    # ---------- columns ----------

    @display(description=_('Post'), header=True, ordering='title')
    def post_header(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.email]

    @display(description=_('Status'), label=STATUS_LABELS, ordering='status')
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description=_('Tags'), dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict:
        # tags.all() uses the prefetched data; tags.count() would not.
        tags = obj.tags.all()
        return {
            'title': _('%d tags') % len(tags),
            'items': [{'title': tag.name} for tag in tags],
        }

    @display(description=_('Comments'), ordering='comment_count')
    def comment_count(self, obj: Post) -> int:
        return obj.comment_count

    # ---------- bulk actions (checkboxes) ----------

    @action(description=_('Publish selected'), icon='publish')
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        # update() does not call save(), so updated_at is set by hand.
        updated = queryset.update(
            status=Post.Status.PUBLISHED,
            updated_at=timezone.now(),
        )
        self.message_user(request, _('%d posts published.') % updated)

    @action(description=_('Move to drafts'), icon='draft')
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(
            status=Post.Status.DRAFT,
            updated_at=timezone.now(),
        )
        self.message_user(request, _('%d posts moved to drafts.') % updated)

    # ---------- row, list, detail and submit line actions ----------

    @action(
        description=_('Publish / unpublish'),
        icon='swap_horiz',
        url_path='toggle-status',
        permissions=[CHANGE_PERMISSION],
    )
    def toggle_status(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        post = Post.objects.get(pk=object_id)
        if post.status == Post.Status.PUBLISHED:
            post.status = Post.Status.DRAFT
        else:
            post.status = Post.Status.PUBLISHED
        post.save(update_fields=['status', 'updated_at'])
        self.message_user(request, _('"%s" is now %s.') % (post.title, post.get_status_display()))
        return HttpResponseRedirect(
            request.headers.get('referer') or reverse('admin:blog_post_changelist')
        )

    @action(
        description=_('Publish all drafts'),
        icon='done_all',
        url_path='publish-all-drafts',
        permissions=[CHANGE_PERMISSION],
    )
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        updated = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED,
            updated_at=timezone.now(),
        )
        self.message_user(request, _('%d drafts published.') % updated)
        return HttpResponseRedirect(reverse('admin:blog_post_changelist'))

    @action(description=_('Open comments'), icon='chat', url_path='open-comments')
    def open_comments(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        url = reverse('admin:blog_comment_changelist')
        return HttpResponseRedirect(f'{url}?post__id__exact={object_id}')

    @action(description=_('Save & publish'), permissions=[CHANGE_PERMISSION])
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        # Runs after the object is saved.
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=['status', 'updated_at'])
