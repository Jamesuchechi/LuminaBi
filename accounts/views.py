"""
Account management views for LuminaBI.
Handles registration, login, profile management, and password reset.
"""

import logging
import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, FormView
from django.views.generic.edit import FormMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.html import format_html
from django.template.loader import render_to_string
from django import forms

from .models import UserProfile, EmailVerification, PasswordReset, LoginHistory, InvitationToken

logger = logging.getLogger(__name__)


# ============================================================================
# FORMS
# ============================================================================

class RegistrationForm(forms.ModelForm):
    """Registration form for new users."""
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        help_text='Password must be at least 8 characters'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm Password'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email


class LoginForm(forms.Form):
    """Custom login form."""
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False, label='Remember me')


class ProfileForm(forms.ModelForm):
    """User profile edit form."""
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'phone_number', 'role', 'theme', 'language', 'timezone',
                  'email_notifications', 'email_digest', 'email_updates']


class PasswordChangeForm(forms.Form):
    """Password change form."""
    old_password = forms.CharField(widget=forms.PasswordInput, label='Current Password')
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label='New Password',
        help_text='Password must be at least 8 characters'
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm New Password'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('New passwords do not match')
        
        return cleaned_data


class PasswordResetForm(forms.Form):
    """Password reset request form."""
    email = forms.EmailField()


class PasswordResetConfirmForm(forms.Form):
    """Password reset confirmation form."""
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label='New Password'
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm New Password'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class LandingPageView(TemplateView):
    """Landing page view - shows to unauthenticated users, redirects authenticated to dashboard."""
    template_name = 'index.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to dashboard."""
        if request.user.is_authenticated:
            return redirect('core:index')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add context for landing page."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'LuminaBI - Data Analytics Made Simple'
        return context


class RegisterView(FormView):
    """User registration view."""
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        # Create user
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data.get('first_name', ''),
            last_name=form.cleaned_data.get('last_name', ''),
        )
        
        # Create email verification token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Send verification email
        try:
            verification_url = self.request.build_absolute_uri(
                f'/accounts/verify-email/{token}/'
            )
            send_verification_email(user, verification_url)
            messages.success(
                self.request,
                'Registration successful! Please check your email to verify your account.'
            )
        except Exception as e:
            logger.error(f'Error sending verification email: {e}')
            messages.warning(
                self.request,
                'Account created but we could not send verification email.'
            )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Account'
        return context


class LoginView(FormView):
    """User login view."""
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core:index')
    
    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            # Record login history
            ip_address = self.get_client_ip()
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')
            
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # Update profile login count
            user.profile.login_count += 1
            user.profile.last_login_ip = ip_address
            user.profile.save()
            
            # Login user
            login(self.request, user)
            
            # Set remember me cookie
            if not form.cleaned_data.get('remember_me'):
                self.request.session.set_expiry(0)
            
            messages.success(self.request, f'Welcome back, {user.username}!')
            return super().form_valid(form)
        else:
            # Record failed login
            try:
                failed_user = User.objects.get(username=username)
                LoginHistory.objects.create(
                    user=failed_user,
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    success=False,
                    reason='Invalid password'
                )
            except User.DoesNotExist:
                pass
            
            messages.error(self.request, 'Invalid username or password')
            return self.form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Login'
        return context


class LogoutView(LoginRequiredMixin, TemplateView):
    """User logout view."""
    template_name = 'accounts/logout.html'
    login_url = 'accounts:login'
    
    def get(self, request, *args, **kwargs):
        # Record logout in login history
        last_login = LoginHistory.objects.filter(user=request.user, logout_at__isnull=True).first()
        if last_login:
            last_login.logout_at = timezone.now()
            last_login.save()
        
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

def verify_email(request, token):
    """Verify user email with token."""
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if not verification.is_valid:
            messages.error(request, 'Verification link has expired or already used.')
            return redirect('accounts:login')
        
        # Mark as verified
        verification.verified = True
        verification.verified_at = timezone.now()
        verification.save()
        
        # Update user profile
        verification.user.profile.is_email_verified = True
        verification.user.profile.email_verified_at = timezone.now()
        verification.user.profile.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')
    
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:register')


# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view."""
    model = UserProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'
    login_url = 'accounts:login'
    
    def get_object(self):
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Profile'
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile."""
    model = UserProfile
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = 'accounts:login'
    
    def get_object(self):
        return self.request.user.profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Profile'
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """View another user's profile."""
    model = User
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile_user'
    login_url = 'accounts:login'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['profile'] = user.profile
        context['page_title'] = f"{user.get_full_name() or user.username}'s Profile"
        return context


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

class PasswordChangeView(LoginRequiredMixin, FormView):
    """Change password view."""
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        user = self.request.user
        old_password = form.cleaned_data['old_password']
        new_password = form.cleaned_data['new_password']
        
        if not user.check_password(old_password):
            messages.error(self.request, 'Current password is incorrect.')
            return self.form_invalid(form)
        
        user.set_password(new_password)
        user.save()
        
        # Re-authenticate user
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Change Password'
        return context


class PasswordResetView(FormView):
    """Request password reset."""
    template_name = 'accounts/password_reset.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Create reset token
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)
            
            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Send reset email
            reset_url = self.request.build_absolute_uri(
                f'/accounts/password-reset/{token}/'
            )
            send_password_reset_email(user, reset_url)
            
            logger.info(f'Password reset requested for {email}')
            
        except User.DoesNotExist:
            # Don't reveal if email exists
            logger.warning(f'Password reset requested for non-existent email: {email}')
        
        messages.info(
            self.request,
            'If an account exists with this email, you will receive a password reset link.'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Password'
        return context


class PasswordResetDoneView(TemplateView):
    """Password reset done confirmation."""
    template_name = 'accounts/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Password Reset'
        return context


class PasswordResetConfirmView(FormView):
    """Confirm password reset with token."""
    template_name = 'accounts/password_reset_confirm.html'
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def get_reset_token(self):
        """Get and validate reset token."""
        token = self.kwargs.get('token')
        try:
            reset = PasswordReset.objects.get(token=token)
            if reset.is_valid:
                return reset
        except PasswordReset.DoesNotExist:
            pass
        return None
    
    def get(self, request, *args, **kwargs):
        reset = self.get_reset_token()
        if not reset:
            messages.error(request, 'Password reset link is invalid or has expired.')
            return redirect('accounts:password_reset')
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        reset = self.get_reset_token()
        if not reset:
            messages.error(self.request, 'Password reset link is invalid or has expired.')
            return redirect('accounts:password_reset')
        
        user = reset.user
        new_password = form.cleaned_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset.used = True
        reset.used_at = timezone.now()
        reset.save()
        
        logger.info(f'Password reset completed for {user.email}')
        messages.success(self.request, 'Password reset successful! You can now log in.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Password'
        return context


class PasswordResetCompleteView(TemplateView):
    """Password reset completion confirmation."""
    template_name = 'accounts/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Password Reset Complete'
        return context


# ============================================================================
# ORGANIZATION INVITATIONS
# ============================================================================

class InvitationAcceptView(LoginRequiredMixin, TemplateView):
    """Accept organization invitation."""
    template_name = 'accounts/invitation_accept.html'
    login_url = 'accounts:login'
    
    def get_invitation(self):
        """Get invitation by token."""
        token = self.kwargs.get('token')
        try:
            invitation = InvitationToken.objects.get(token=token)
            if invitation.is_valid and invitation.email == self.request.user.email:
                return invitation
        except InvitationToken.DoesNotExist:
            pass
        return None
    
    def get(self, request, *args, **kwargs):
        invitation = self.get_invitation()
        if not invitation:
            messages.error(request, 'Invitation is invalid or has expired.')
            return redirect('core:organization_list')
        
        context = self.get_context_data(**kwargs)
        context['invitation'] = invitation
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        invitation = self.get_invitation()
        if not invitation:
            messages.error(request, 'Invitation is invalid or has expired.')
            return redirect('core:organization_list')
        
        # Add user to organization
        invitation.organization.members.add(request.user)
        
        # Mark invitation as accepted
        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.accepted_by = request.user
        invitation.save()
        
        messages.success(
            request,
            f'You have joined {invitation.organization.name}!'
        )
        
        return redirect('core:organization_detail', pk=invitation.organization.pk)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_verification_email(user, verification_url):
    """Send email verification link."""
    subject = 'Verify your LuminaBI email'
    message = render_to_string('accounts/emails/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    send_mail(
        subject,
        message,
        'noreply@luminabi.com',
        [user.email],
        html_message=message,
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """Send password reset link."""
    subject = 'Reset your LuminaBI password'
    message = render_to_string('accounts/emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    send_mail(
        subject,
        message,
        'noreply@luminabi.com',
        [user.email],
        html_message=message,
        fail_silently=False,
    )
