"""
User account models for LuminaBI.
Extends Django's built-in User model with profile and preference management.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile with organization context and preferences.
    """
    
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('analyst', 'Data Analyst'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile information
    bio = models.TextField(blank=True, null=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number'
            )
        ]
    )
    
    # Role and permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    
    # Preferences
    theme = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French')],
        default='en'
    )
    timezone = models.CharField(
        max_length=50,
        choices=[
            ('UTC', 'UTC'),
            ('US/Eastern', 'Eastern Time'),
            ('US/Central', 'Central Time'),
            ('US/Mountain', 'Mountain Time'),
            ('US/Pacific', 'Pacific Time'),
        ],
        default='UTC'
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    email_digest = models.BooleanField(default=True, help_text='Receive weekly digest emails')
    email_updates = models.BooleanField(default=True, help_text='Receive important updates')
    
    # Subscription preferences
    preferred_subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('individual', 'Individual'),
            ('team', 'Team'),
            ('business', 'Business'),
            ('enterprise', 'Enterprise'),
        ],
        default='individual',
        help_text='Preferred subscription tier selected during registration'
    )
    
    # Tier-specific information
    team_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Team name for Team and Team Plus tiers'
    )
    team_size = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('1-5', '1-5 members'),
            ('5-10', '5-10 members'),
            ('10-25', '10-25 members'),
            ('25-50', '25-50 members'),
            ('50+', '50+ members'),
        ],
        help_text='Team size for Team and Team Plus tiers'
    )
    business_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Business name for Business and Enterprise tiers'
    )
    business_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Business location (city, country)'
    )
    business_industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Industry or business sector'
    )
    enterprise_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Enterprise company name'
    )
    enterprise_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Enterprise headquarters location (city, country)'
    )
    enterprise_industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Enterprise industry or business sector'
    )
    enterprise_size = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('100-500', '100-500 employees'),
            ('500-1000', '500-1,000 employees'),
            ('1000-5000', '1,000-5,000 employees'),
            ('5000+', '5,000+ employees'),
        ],
        help_text='Enterprise company size'
    )
    enterprise_contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Enterprise technical contact email'
    )
    
    # Account tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_count = models.IntegerField(default=0)
    
    # Account status
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_user_profile'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    @property
    def full_name(self):
        """Return user's full name or username."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def display_name(self):
        """Return display name for templates."""
        return self.full_name or self.user.email


class EmailVerification(models.Model):
    """
    Email verification tokens for new accounts.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_email_verification'
    
    def __str__(self):
        return f'Email verification for {self.user.email}'
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and not expired."""
        return not self.is_expired and not self.verified


class PasswordReset(models.Model):
    """
    Password reset tokens.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_password_reset'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Password reset for {self.user.email}'
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and not expired."""
        return not self.is_expired and not self.used


class LoginHistory(models.Model):
    """
    Track user login activities for security auditing.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(blank=True, null=True)
    success = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_login_history'
        ordering = ['-login_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.login_at}'
    
    @property
    def duration(self):
        """Calculate session duration."""
        if self.logout_at:
            return self.logout_at - self.login_at
        return timezone.now() - self.login_at


class InvitationToken(models.Model):
    """
    Invitation tokens for joining organizations.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    from core.models import Organization
    
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    token = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_invitations')
    
    class Meta:
        db_table = 'accounts_invitation_token'
        ordering = ['-created_at']
        unique_together = ('organization', 'email')
    
    def __str__(self):
        return f'Invitation to {self.email} for {self.organization.name}'
    
    @property
    def is_expired(self):
        """Check if invitation has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if invitation is valid and can be accepted."""
        return self.status == 'pending' and not self.is_expired


# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    instance.profile.save()
