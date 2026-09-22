from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import AdminUserCreationForm
from .models import CustomUser, LoginHistory


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    list_display = ('email', 'get_full_name', 'role', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'is_deleted')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Information'), {'fields': (
            'first_name', 'last_name', 'username', 'avatar', 'bio',
            'phone_number', 'date_of_birth', 'gender', 'country', 'state', 'city',
            'favorite_team', 'favorite_player',
        )}),
        (_('Permissions & Roles'), {'fields': (
            'role', 'is_active', 'is_staff',
            'is_superuser', 'is_deleted', 'groups', 'user_permissions',
        )}),
        (_('Security'), {'fields': (
            'failed_login_attempts',
            'locked_until', 'last_login_ip', 'last_login_user_agent',
        ), 'classes': ('collapse',)}),
        (_('Important Dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': (
            'email', 'first_name', 'last_name', 'username', 'role', 'password1', 'password2',
        )}),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'successful', 'ip_address', 'created_at')
    list_filter = ('successful', 'created_at')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('user', 'successful', 'ip_address', 'user_agent', 'created_at')
