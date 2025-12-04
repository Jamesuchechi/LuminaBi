"""
Permission mixins for LuminaBI core application.
Provides reusable access control and authorization functionality.
"""

import logging
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import Http404, JsonResponse
from .models import Organization

logger = logging.getLogger(__name__)


class SuperUserRequiredMixin(AccessMixin):
    """
    Mixin that requires the user to be a superuser.
    Redirects to login if not authenticated, denies access if not superuser.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())
        
        if not request.user.is_superuser:
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied'}, status=403)
            raise Http404('Access denied')
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(AccessMixin):
    """
    Mixin that requires the user to be staff or superuser.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())
        
        if not (request.user.is_staff or request.user.is_superuser):
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied'}, status=403)
            raise Http404('Access denied')
        
        return super().dispatch(request, *args, **kwargs)


class OrganizationAccessMixin:
    """
    Mixin that checks if user has access to an organization.
    Used for organization-specific views.
    """
    
    def get_organization(self):
        """Get the organization from URL kwargs."""
        org_id = self.kwargs.get('org_id') or self.kwargs.get('pk')
        try:
            org = Organization.objects.get(id=org_id)
            return org
        except Organization.DoesNotExist:
            raise Http404('Organization not found')
    
    def check_organization_access(self):
        """Check if user is member of the organization."""
        org = self.get_organization()
        
        if not org.members.filter(id=self.request.user.id).exists() and \
           org.owner != self.request.user:
            if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied'}, status=403)
            raise Http404('Access denied')
        
        return org
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        self.organization = self.check_organization_access()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.organization
        return context


class OrganizationOwnerMixin(OrganizationAccessMixin):
    """
    Mixin that checks if user is the owner of an organization.
    Used for edit/delete operations.
    """
    
    def check_organization_access(self):
        """Check if user is the owner of the organization."""
        org = self.get_organization()
        
        if org.owner != self.request.user:
            if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Only owner can perform this action'}, status=403)
            raise Http404('Access denied')
        
        return org


class OrganizationMemberMixin(OrganizationAccessMixin):
    """
    Mixin that checks if user is a member of an organization.
    Used for view-only operations.
    """
    pass


class AuditLogAccessMixin(SuperUserRequiredMixin):
    """
    Mixin for audit log access.
    Only superusers can view audit logs.
    """
    pass


class SettingsAccessMixin(SuperUserRequiredMixin):
    """
    Mixin for settings access.
    Only superusers can manage settings.
    """
    pass


class AjaxRequiredMixin:
    """
    Mixin that restricts access to AJAX requests only.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return super().dispatch(request, *args, **kwargs)


class OwnerRequiredMixin:
    """
    Mixin that checks if the user is the owner of an object.
    Requires the model to have an 'owner' field.
    """
    
    def get_queryset(self):
        """Filter queryset to only include objects owned by the current user."""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(owner=self.request.user)
        return queryset
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)


class PublicAccessMixin:
    """
    Mixin for public views that may or may not require authentication.
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_authenticated'] = self.request.user.is_authenticated
        return context


class RateLimitMixin:
    """
    Mixin for rate limiting requests.
    Can be extended with actual rate limiting logic.
    """
    
    rate_limit_key = 'rate_limit'
    rate_limit_attempts = 100
    rate_limit_period = 3600  # 1 hour
    
    def check_rate_limit(self):
        """Check if user has exceeded rate limit."""
        from django.core.cache import cache
        
        if not self.request.user.is_authenticated:
            cache_key = f'rate_limit:{self.request.META.get("REMOTE_ADDR")}'
        else:
            cache_key = f'rate_limit:{self.request.user.id}'
        
        attempts = cache.get(cache_key, 0)
        if attempts >= self.rate_limit_attempts:
            return False
        
        cache.set(cache_key, attempts + 1, self.rate_limit_period)
        return True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.check_rate_limit():
            return JsonResponse(
                {'error': 'Rate limit exceeded'},
                status=429
            )
        return super().dispatch(request, *args, **kwargs)
