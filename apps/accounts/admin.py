from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'nickname', 'gender', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'gender']
    search_fields = ['email', 'nickname']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('个人信息', {'fields': ('nickname', 'avatar', 'gender', 'training_frequency', 'session_duration_minutes', 'focus_area')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('时间', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used']
