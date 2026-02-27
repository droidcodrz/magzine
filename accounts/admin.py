from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'get_full_name', 'role', 'is_staff', 'is_verified', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_verified', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'bio', 'avatar')}),
        ('Role & Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
