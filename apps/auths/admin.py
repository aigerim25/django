from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.auths.models import User

ACTIVE_LABELS = {True: 'success', False: 'danger'}
STAFF_LABELS = {True: 'info', False: 'warning'}
YES_NO = {True: _('Yes'), False: _('No')}

# Our User has no `username`. Django's admin forms and UserAdmin mention it,
# so the forms are subclassed with our model and fields.


class BlogUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name')
        field_classes = {}


class BlogUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'
        field_classes = {}


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ('user_header', 'active_label', 'staff_label', 'post_count')
    list_filter = (
        ('is_active', BooleanRadioFilter),
        ('is_staff', BooleanRadioFilter),
    )
    list_filter_submit = True
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('last_login',)
    actions = ('activate_users', 'deactivate_users')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'classes': ['tab'],
            'fields': ('first_name', 'last_name'),
        }),
        (_('Permissions'), {
            'classes': ['tab'],
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {
            'classes': ['tab'],
            'fields': ('last_login',),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(post_count=Count('post'))

    @display(description=_('User'), header=True, ordering='email')
    def user_header(self, obj: User) -> list[str]:
        initials = f'{obj.first_name[:1]}{obj.last_name[:1]}'
        return [obj.get_full_name(), obj.email, initials]

    @display(description=_('Active'), label=ACTIVE_LABELS)
    def active_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, YES_NO[obj.is_active]

    @display(description=_('Staff'), label=STAFF_LABELS)
    def staff_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, YES_NO[obj.is_staff]

    @display(description=_('Posts'), ordering='post_count')
    def post_count(self, obj: User) -> int:
        return obj.post_count

    @action(description=_('Activate selected users'), icon='check_circle')
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, _('%d users activated.') % updated)

    @action(description=_('Deactivate selected users'), icon='block')
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, _('%d users deactivated.') % updated)
