"""
Admin configuration for the accounts application.
"""

from django.contrib import admin
from .models import UserProfile, EmailVerification, PasswordReset, LoginHistory, InvitationToken


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ['user', 'role', 'is_email_verified', 'login_count', 'created_at']
    list_filter = ['role', 'is_email_verified', 'theme', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'login_count', 'email_verified_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile', {
            'fields': ('bio', 'avatar', 'phone_number', 'role')
        }),
        ('Preferences', {
            'fields': ('theme', 'language', 'timezone')
        }),
        ('Email Preferences', {
            'fields': ('email_notifications', 'email_digest', 'email_updates')
        }),
        ('Account Status', {
            'fields': ('is_email_verified', 'email_verified_at')
        }),
        ('Login Information', {
            'fields': ('login_count', 'last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Admin for EmailVerification model."""
    list_display = ['user', 'verified', 'created_at', 'expires_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at', 'expires_at', 'verified_at']


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin for PasswordReset model."""
    list_display = ['user', 'used', 'created_at', 'expires_at']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at', 'expires_at', 'used_at']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for LoginHistory model."""
    list_display = ['user', 'success', 'ip_address', 'login_at', 'logout_at']
    list_filter = ['success', 'login_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_at', 'logout_at', 'user_agent']


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    """Admin for InvitationToken model."""
    list_display = ['email', 'organization', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at', 'organization']
    search_fields = ['email', 'organization__name']
    readonly_fields = ['token', 'created_at', 'accepted_at']
