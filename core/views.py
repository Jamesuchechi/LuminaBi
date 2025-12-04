"""
Class-based views for LuminaBI core application.
Handles organizations, settings, audit logs, and system configuration.
"""

import logging
import json
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from .models import Organization, Setting, AuditLog
from .serializers import OrganizationSerializer, SettingSerializer

logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_action(action, user, **kwargs):
    """Log an action to the audit log."""
    try:
        AuditLog.objects.create(
            action=action,
            user=user,
            **kwargs
        )
    except Exception as e:
        logger.error(f'Error logging action: {e}')


def get_setting(key, default=None):
    """Get a setting value by key."""
    try:
        setting = Setting.objects.get(key=key)
        return setting.value
    except Setting.DoesNotExist:
        return default


def set_setting(key, value):
    """Set a setting value by key."""
    setting, created = Setting.objects.get_or_create(key=key)
    setting.value = value
    setting.save()
    return setting


# ============================================================================
# ORGANIZATION VIEWS
# ============================================================================

class OrganizationListView(LoginRequiredMixin, ListView):
    """
    List all organizations for the current user.
    Shows owned and member organizations.
    """
    model = Organization
    template_name = 'core/organization/list.html'
    context_object_name = 'organizations'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get user's organizations (owned or member)."""
        user = self.request.user
        return Organization.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['owned_organizations'] = Organization.objects.filter(owner=user).count()
        context['member_organizations'] = Organization.objects.filter(
            members=user
        ).exclude(owner=user).count()
        
        # Action logging
        log_action('viewed_organizations', self.request.user)
        
        return context


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new organization.
    Current user becomes the owner.
    """
    model = Organization
    template_name = 'core/organization/form.html'
    fields = ['name']
    success_url = reverse_lazy('core:organization_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        
        # Add owner as member
        self.object.members.add(self.request.user)
        
        # Log action
        log_action('created_organization', self.request.user)
        
        return response


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    """
    Display organization details, members, and settings.
    """
    model = Organization
    template_name = 'core/organization/detail.html'
    context_object_name = 'organization'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show organizations user is part of."""
        user = self.request.user
        return Organization.objects.filter(
            Q(owner=user) | Q(members=user)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        
        context['is_owner'] = org.owner == self.request.user
        context['members'] = org.members.all()
        
        # Log action
        log_action('viewed_organization_detail', self.request.user)
        
        return context


class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update organization details.
    Only accessible to the owner.
    """
    model = Organization
    template_name = 'core/organization/form.html'
    fields = ['name']
    success_url = reverse_lazy('core:organization_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to update."""
        return Organization.objects.filter(owner=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_action('updated_organization', self.request.user)
        return response


class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete an organization.
    Only accessible to the owner.
    """
    model = Organization
    template_name = 'core/organization/confirm_delete.html'
    success_url = reverse_lazy('core:organization_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to delete."""
        return Organization.objects.filter(owner=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        log_action('deleted_organization', self.request.user)
        return super().delete(request, *args, **kwargs)


# ============================================================================
# SETTINGS VIEWS
# ============================================================================

class SettingsListView(LoginRequiredMixin, ListView):
    """
    List all system settings (admin only).
    """
    model = Setting
    template_name = 'core/settings/list.html'
    context_object_name = 'settings'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only superusers can view all settings."""
        if not self.request.user.is_superuser:
            return Setting.objects.none()
        return Setting.objects.all().order_by('key')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('core:index')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_action('viewed_settings', self.request.user)
        return context


class SettingsUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update a system setting (admin only).
    """
    model = Setting
    template_name = 'core/settings/form.html'
    fields = ['value']
    success_url = reverse_lazy('core:settings_list')
    login_url = 'accounts:login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('core:index')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_action('updated_setting', self.request.user)
        return response


# ============================================================================
# AUDIT LOG VIEWS
# ============================================================================

class AuditLogListView(LoginRequiredMixin, ListView):
    """
    List audit logs (admin only).
    Shows all user actions.
    """
    model = AuditLog
    template_name = 'core/audit/list.html'
    context_object_name = 'audit_logs'
    paginate_by = 50
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only superusers can view audit logs."""
        if not self.request.user.is_superuser:
            return AuditLog.objects.none()
        return AuditLog.objects.all().order_by('-timestamp')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('core:index')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter options
        context['action_filter'] = self.request.GET.get('action', '')
        context['user_filter'] = self.request.GET.get('user', '')
        
        log_action('viewed_audit_logs', self.request.user)
        return context


# ============================================================================
# API VIEWS (JSON endpoints)
# ============================================================================

class OrganizationAPIView(LoginRequiredMixin, DetailView):
    """
    JSON API endpoint for organization data.
    """
    model = Organization
    login_url = 'accounts:login'
    
    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(
            Q(owner=user) | Q(members=user)
        )
    
    def get(self, request, *args, **kwargs):
        org = self.get_object()
        serializer = OrganizationSerializer(org)
        return JsonResponse(serializer.data)


class SettingAPIView(LoginRequiredMixin, DetailView):
    """
    JSON API endpoint for getting/setting configuration values.
    """
    login_url = 'accounts:login'
    
    def get(self, request, *args, **kwargs):
        """Get a setting value."""
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        key = kwargs.get('key')
        try:
            setting = Setting.objects.get(key=key)
            return JsonResponse({
                'key': setting.key,
                'value': setting.value,
                'site_wide': setting.site_wide,
                'updated_at': setting.updated_at.isoformat(),
            })
        except Setting.DoesNotExist:
            return JsonResponse({'error': 'Setting not found'}, status=404)
    
    def post(self, request, *args, **kwargs):
        """Update a setting value."""
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        key = kwargs.get('key')
        try:
            data = json.loads(request.body)
            setting = set_setting(key, data.get('value'))
            log_action('updated_setting_via_api', request.user)
            return JsonResponse({
                'success': True,
                'message': 'Setting updated'
            })
        except Exception as e:
            logger.error(f'Error updating setting: {e}')
            return JsonResponse({'error': str(e)}, status=400)


class HealthCheckView(TemplateView):
    """
    System health check endpoint.
    Returns status of core services.
    """
    def get(self, request, *args, **kwargs):
        from django.db import connection
        from django.core.cache import cache
        
        status_data = {
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': 'down',
                'cache': 'down',
                'scheduler': 'down',
            }
        }
        
        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            status_data['services']['database'] = 'up'
        except Exception as e:
            logger.error(f'Database health check failed: {e}')
            status_data['status'] = 'degraded'
        
        # Check cache
        try:
            cache.set('health_check', 'ok', 1)
            status_data['services']['cache'] = 'up'
        except Exception as e:
            logger.warning(f'Cache health check failed: {e}')
        
        # Check scheduler
        try:
            from core.scheduler import get_scheduler_jobs
            jobs = get_scheduler_jobs()
            if jobs is not None:
                status_data['services']['scheduler'] = 'up'
        except Exception as e:
            logger.warning(f'Scheduler health check failed: {e}')
        
        http_status = 200 if status_data['status'] == 'ok' else 503
        return JsonResponse(status_data, status=http_status)


class SystemStatsView(LoginRequiredMixin, TemplateView):
    """
    System statistics endpoint (admin only).
    Returns metrics about system usage.
    """
    login_url = 'accounts:login'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        from django.contrib.auth.models import User
        
        stats = {
            'total_users': User.objects.count(),
            'total_organizations': Organization.objects.count(),
            'total_settings': Setting.objects.count(),
            'recent_actions': AuditLog.objects.count(),
            'audit_logs_7days': AuditLog.objects.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        log_action('viewed_system_stats', request.user)
        return JsonResponse(stats)


# ============================================================================
# API VIEWSETS
# ============================================================================

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

class OrganizationViewSet(viewsets.ModelViewSet):
    """API ViewSet for Organization model."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter organizations by user membership."""
        return Organization.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the organization."""
        org = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            org.members.add(user)
            return Response({'status': 'member added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the organization."""
        org = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            org.members.remove(user)
            return Response({'status': 'member removed'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class SettingViewSet(viewsets.ModelViewSet):
    """API ViewSet for Setting model."""
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter settings by user's organization."""
        user_orgs = Organization.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        )
        return Setting.objects.filter(
            Q(site_wide=True) | Q(organization__in=user_orgs)
        )




