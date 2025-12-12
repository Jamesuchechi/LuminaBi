"""
Class-based views for LuminaBI core application.
Handles organizations, settings, audit logs, system configuration, and dashboards.
"""

import logging
import json
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from .models import (
    Organization, Setting, AuditLog, Notification,
    Dashboard, DashboardWidget, DashboardInsight, InterpretabilityAnalysis, DashboardShare
)
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
    try:
        setting, _ = Setting.objects.get_or_create(key=key)
        setting.value = value
        setting.save()
        return True
    except Exception as e:
        logger.error(f'Error setting value: {e}')
        return False


def create_notification(user, title, message, notification_type='info', related_app=None, related_model=None, related_object_id=None):
    """
    Create a notification for a user.
    
    Args:
        user: User object or user ID
        title: Notification title
        message: Notification message
        notification_type: 'info', 'success', 'warning', or 'error'
        related_app: Related app name (e.g., 'datasets')
        related_model: Related model name (e.g., 'Dataset')
        related_object_id: ID of related object
    """
    try:
        from django.contrib.auth.models import User
        
        if isinstance(user, int):
            user = User.objects.get(pk=user)
        
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_app=related_app,
            related_model=related_model,
            related_object_id=related_object_id,
        )
        
        logger.info(f'Notification created for {user.username}: {title}')
        return notification
    except Exception as e:
        logger.error(f'Error creating notification: {e}')
        return None
    setting, created = Setting.objects.get_or_create(key=key)
    setting.value = value
    setting.save()
    return setting


# ============================================================================
# INDEX & HOME VIEW
# ============================================================================

class IndexView(LoginRequiredMixin, TemplateView):
    """Home/index page for authenticated users with live analytics."""
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        """Add dashboard statistics and live analytics to context."""
        from datasets.models import Dataset
        from insights.models import DataInsight, AnomalyDetection, OutlierAnalysis, RelationshipAnalysis
        from analytics.models import Insight as AnalyticsInsight
        from visualizations.models import Visualization
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        from django.core.paginator import Paginator
        
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User's datasets, analytics, insights, and visualizations
        user_datasets = Dataset.objects.filter(owner=user).order_by('-uploaded_at')
        user_visualizations = Visualization.objects.filter(owner=user).order_by('-created_at')
        user_analytics_insights = AnalyticsInsight.objects.filter(dataset__owner=user).order_by('-created_at')
        user_data_insights = DataInsight.objects.filter(dataset__owner=user).order_by('-created_at')
        
        # ======= LIVE STATISTICS =======
        context['total_datasets'] = user_datasets.count()
        context['cleaned_datasets'] = user_datasets.filter(is_cleaned=True).count()
        context['total_visualizations'] = user_visualizations.count()
        context['total_analytics_insights'] = user_analytics_insights.count()
        context['total_data_insights'] = user_data_insights.count()
        
        # ======= DATASETS SECTION (Paginated - 3 items) =======
        datasets_paginator = Paginator(user_datasets, 3)
        context['datasets_page'] = datasets_paginator.get_page(self.request.GET.get('datasets_page', 1))
        context['datasets_total'] = user_datasets.count()
        
        # ======= ANALYTICS INSIGHTS SECTION (Paginated - 3 items) =======
        analytics_paginator = Paginator(user_analytics_insights, 3)
        context['analytics_page'] = analytics_paginator.get_page(self.request.GET.get('analytics_page', 1))
        context['analytics_total'] = user_analytics_insights.count()
        
        # ======= DATA INSIGHTS SECTION (Paginated - 3 items) =======
        data_insights_paginator = Paginator(user_data_insights, 3)
        context['insights_page'] = data_insights_paginator.get_page(self.request.GET.get('insights_page', 1))
        context['insights_total'] = user_data_insights.count()
        
        # ======= VISUALIZATIONS SECTION (Paginated - 3 items) =======
        visualizations_paginator = Paginator(user_visualizations, 3)
        context['visualizations_page'] = visualizations_paginator.get_page(self.request.GET.get('visualizations_page', 1))
        context['visualizations_total'] = user_visualizations.count()
        
        # ======= DATA HEALTH & ANOMALIES =======
        anomalies = AnomalyDetection.objects.filter(dataset__owner=user)
        context['total_anomalies'] = anomalies.count()
        context['critical_anomalies'] = anomalies.filter(severity='critical').count()
        
        # Calculate data health score
        total_datasets_count = user_datasets.count()
        if total_datasets_count > 0:
            context['data_health_score'] = int((user_datasets.filter(is_cleaned=True).count() / total_datasets_count) * 100)
        else:
            context['data_health_score'] = 0
        
        # ======= INSIGHTS BREAKDOWN =======
        context['insight_cards'] = {
            'found': user_data_insights.filter(insight_type='anomaly').count(),
            'detected': anomalies.count(),
            'health': context['data_health_score'],
        }
        
        # ======= TIMELINE DATA (30 days) =======
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_datasets = []
        daily_labels = []
        
        for i in range(30):
            day = timezone.now() - timedelta(days=29-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = user_datasets.filter(
                uploaded_at__range=[day_start, day_end]
            ).count()
            daily_datasets.append(count)
            daily_labels.append(day.strftime('%m/%d'))
        
        context['datasets_timeline'] = {
            'labels': daily_labels,
            'data': daily_datasets,
        }
        
        # ======= INSIGHTS TYPE DISTRIBUTION =======
        insight_types = {
            'anomalies': anomalies.count(),
            'outliers': OutlierAnalysis.objects.filter(dataset__owner=user).count(),
            'correlations': RelationshipAnalysis.objects.filter(dataset__owner=user).count(),
            'analytics': user_analytics_insights.count(),
        }
        context['insight_distribution'] = insight_types
        
        return context


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

class UserSettingsView(LoginRequiredMixin, UpdateView):
    """
    User preference settings (theme, language, timezone).
    All authenticated users can access and modify their own settings.
    """
    model = User
    template_name = 'core/user_settings.html'
    fields = []
    login_url = 'accounts:login'
    success_url = reverse_lazy('core:user_settings')
    
    def get_object(self):
        """Return the current user's profile."""
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        """Add preference options to context."""
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        
        context['profile'] = profile
        context['theme_choices'] = [
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto (System)'),
        ]
        context['language_choices'] = [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
        ]
        context['timezones'] = [
            'UTC', 'America/New_York', 'America/Chicago', 'America/Los_Angeles',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin',
            'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong',
            'Australia/Sydney', 'Australia/Melbourne',
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle settings update via form submission."""
        try:
            profile = self.request.user.profile
            
            # Update theme if provided
            if 'theme' in request.POST:
                profile.theme = request.POST.get('theme')
            
            # Update language if provided
            if 'language' in request.POST:
                profile.language = request.POST.get('language')
            
            # Update timezone if provided
            if 'timezone' in request.POST:
                profile.timezone = request.POST.get('timezone')
            
            profile.save()
            
            # Log the action
            log_action('updated_preferences', request.user)
            
            # Create notification
            create_notification(
                request.user,
                'Settings Updated',
                'Your preferences have been saved successfully.',
                notification_type='success'
            )
            
            return redirect('core:user_settings')
        except Exception as e:
            logger.error(f'Error updating user settings: {e}')
            return redirect('core:user_settings')


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
# NOTIFICATION VIEWS
# ============================================================================

class UnreadNotificationsAPIView(LoginRequiredMixin, TemplateView):
    """Get count of unread notifications for current user."""
    login_url = 'accounts:login'
    
    def get(self, request, *args, **kwargs):
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        notifications_data = []
        for notif in unread_notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'created_at': notif.created_at.isoformat(),
                'related_app': notif.related_app,
                'related_object_id': notif.related_object_id,
            })
        
        return JsonResponse({
            'unread_count': unread_count,
            'unread_notifications': notifications_data
        })


class NotificationsListAPIView(LoginRequiredMixin, TemplateView):
    """Get all notifications for current user with pagination."""
    login_url = 'accounts:login'
    
    def get(self, request, *args, **kwargs):
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        total_count = notifications.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_notifications = notifications[start:end]
        
        notifications_data = []
        for notif in paginated_notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'read_at': notif.read_at.isoformat() if notif.read_at else None,
                'related_app': notif.related_app,
                'related_object_id': notif.related_object_id,
            })
        
        return JsonResponse({
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'notifications': notifications_data,
            'has_next': end < total_count
        })


class NotificationMarkReadAPIView(LoginRequiredMixin, TemplateView):
    """Mark a specific notification as read."""
    login_url = 'accounts:login'
    
    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.mark_as_read()
            
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read',
                'notification': {
                    'id': notification.id,
                    'is_read': notification.is_read,
                    'read_at': notification.read_at.isoformat() if notification.read_at else None,
                }
            })
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'}, status=404)


# ============================================================================
# NOTIFICATIONS PAGE VIEW
# ============================================================================

class NotificationsPageView(LoginRequiredMixin, TemplateView):
    """Display all notifications for the current user."""
    template_name = 'core/notifications.html'
    login_url = 'accounts:login'
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        """Add notifications and statistics to context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all notifications
        all_notifications = Notification.objects.filter(user=user).order_by('-created_at')
        
        # Pagination
        from django.core.paginator import Paginator
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(all_notifications, self.paginate_by)
        page_obj = paginator.get_page(page_number)
        
        # Statistics
        context['page_obj'] = page_obj
        context['notifications'] = page_obj.object_list
        context['total_notifications'] = all_notifications.count()
        context['unread_count'] = all_notifications.filter(is_read=False).count()
        context['read_count'] = all_notifications.filter(is_read=True).count()
        
        # Group by notification type
        context['by_type'] = {
            'success': all_notifications.filter(notification_type='success').count(),
            'error': all_notifications.filter(notification_type='error').count(),
            'warning': all_notifications.filter(notification_type='warning').count(),
            'info': all_notifications.filter(notification_type='info').count(),
        }
        
        return context


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


# ============================================================================
# DASHBOARD VIEWS (migrated from dashboards app)
# ============================================================================

class DashboardListView(LoginRequiredMixin, ListView):
    """List all dashboards for the current user."""
    model = Dashboard
    template_name = 'dashboards/dashboard/list.html'
    context_object_name = 'dashboards'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get dashboards owned by or shared with user."""
        user = self.request.user
        owned = Q(owner=user)
        shared = Q(shares__shared_with=user, shares__expires_at__gt=timezone.now()) | \
                Q(shares__shared_with=user, shares__expires_at__isnull=True)
        
        return Dashboard.objects.filter(owned | shared).distinct().order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistics
        context['total_dashboards'] = Dashboard.objects.filter(owner=user).count()
        context['published_dashboards'] = Dashboard.objects.filter(
            owner=user, 
            is_published=True
        ).count()
        context['shared_with_me'] = DashboardShare.objects.filter(
            shared_with=user
        ).count()
        context['template_dashboards'] = Dashboard.objects.filter(
            is_template=True
        ).count()

        # Live hub data
        from datasets.models import Dataset
        from analytics.models import Insight, Anomaly, Metric
        
        context['recent_datasets'] = Dataset.objects.filter(
            owner=user
        ).order_by('-uploaded_at')[:6]

        context['recent_insights'] = Insight.objects.filter(
            dataset__owner=user
        ).order_by('-created_at')[:6]

        context['recent_anomalies'] = Anomaly.objects.filter(
            dataset__owner=user
        ).order_by('-detected_at')[:6]

        context['recent_metrics'] = Metric.objects.filter(
            dataset__owner=user
        ).order_by('-updated_at')[:6]
        
        return context


class DashboardDetailView(LoginRequiredMixin, DetailView):
    """
    Display comprehensive dashboard with all widgets, insights, and analytics.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/detail.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_object(self):
        """Get dashboard and check access permissions."""
        obj = super().get_object()
        user = self.request.user
        
        # Check if user owns or has access
        if obj.owner != user:
            share = DashboardShare.objects.filter(
                dashboard=obj,
                shared_with=user
            ).first()
            
            if not share or share.is_expired:
                if not obj.is_published:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("You don't have access to this dashboard")
        
        # Increment view count
        obj.increment_view_count()
        
        # Refresh insights if needed
        if obj.needs_insight_refresh():
            self._refresh_dashboard_insights(obj)
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.get_object()
        user = self.request.user
        
        from analytics.models import Insight, Anomaly, Metric
        
        # Access control
        context['is_owner'] = dashboard.owner == user
        context['can_edit'] = context['is_owner'] or self._user_can_edit(dashboard, user)
        
        # Widgets
        context['widgets'] = dashboard.widgets.filter(is_visible=True).order_by(
            'position_y', 'position_x'
        )
        
        # Visualizations
        visualizations = dashboard.visualizations.all()
        context['visualizations'] = visualizations
        context['visualization_data'] = self._prepare_visualization_data(visualizations)
        
        # Dashboard insights
        context['insights'] = dashboard.dashboard_insights.filter(
            Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True)
        ).order_by('-priority', '-generated_at')[:20]
        
        # Actionable insights
        context['actionable_insights'] = dashboard.dashboard_insights.filter(
            is_actionable=True,
            action_taken=False
        ).order_by('-priority')
        
        # Analytics from related datasets
        datasets = dashboard.datasets.all()
        context['datasets'] = datasets
        context['dataset_insights'] = Insight.objects.filter(
            dataset__in=datasets
        ).order_by('-created_at')[:10]
        
        context['anomalies'] = Anomaly.objects.filter(
            dataset__in=datasets,
            status__in=['new', 'acknowledged', 'investigating']
        ).order_by('-severity', '-detected_at')[:10]
        
        context['metrics'] = Metric.objects.filter(
            dataset__in=datasets
        ).order_by('-updated_at')[:10]
        
        # Interpretability analyses
        if dashboard.interpretability_enabled:
            context['interpretability_analyses'] = dashboard.interpretability_analyses.order_by(
                '-created_at'
            )[:5]

        # Dataset summaries for overview cards
        dataset_summaries = []
        for ds in datasets:
            dataset_summaries.append({
                'id': ds.id,
                'name': ds.name,
                'rows': ds.row_count,
                'cols': ds.col_count,
                'quality': ds.data_quality_score,
                'is_cleaned': ds.is_cleaned,
                'summary': (ds.summary[:180] + '...') if ds.summary and len(ds.summary) > 180 else ds.summary,
                'uploaded_at': ds.uploaded_at,
            })
        context['dataset_summaries'] = dataset_summaries

        # Insights grouped by dataset for quick navigation
        insights_grouped = {}
        for insight in context['dataset_insights']:
            key = insight.dataset_id
            if key not in insights_grouped:
                insights_grouped[key] = []
            insights_grouped[key].append(insight)
        context['insights_grouped'] = insights_grouped
        
        # Summary statistics
        context['summary_stats'] = {
            'total_insights': dashboard.dashboard_insights.count(),
            'critical_insights': dashboard.dashboard_insights.filter(priority='critical').count(),
            'actionable_count': dashboard.dashboard_insights.filter(
                is_actionable=True, 
                action_taken=False
            ).count(),
            'widget_count': dashboard.widgets.count(),
            'visualization_count': visualizations.count(),
            'dataset_count': datasets.count(),
        }
        
        return context
    
    def _user_can_edit(self, dashboard, user):
        """Check if user has edit permissions."""
        share = DashboardShare.objects.filter(
            dashboard=dashboard,
            shared_with=user
        ).first()
        return share and share.can_edit() and not share.is_expired
    
    def _prepare_visualization_data(self, visualizations):
        """Prepare visualization data for Chart.js rendering."""
        vis_data = {}
        for vis in visualizations:
            if vis.config and isinstance(vis.config, dict):
                vis_data[vis.id] = {
                    'title': vis.title,
                    'type': vis.chart_type,
                    'data': vis.config
                }
            else:
                vis_data[vis.id] = {
                    'title': vis.title,
                    'type': vis.chart_type,
                    'data': {
                        'labels': ['Data 1', 'Data 2', 'Data 3'],
                        'datasets': [{
                            'label': vis.title,
                            'data': [10, 20, 30],
                        }]
                    }
                }
        return json.dumps(vis_data)
    
    def _refresh_dashboard_insights(self, dashboard):
        """
        Refresh dashboard insights by analyzing current data.
        """
        try:
            dashboard.last_insight_refresh = timezone.now()
            dashboard.save(update_fields=['last_insight_refresh'])
            
            logger.info(f"Dashboard {dashboard.id} insights marked for refresh")
            
        except Exception as e:
            logger.error(f"Error refreshing insights for dashboard {dashboard.id}: {e}")


class DashboardCreateView(LoginRequiredMixin, CreateView):
    """Create a new dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = [
        'name', 'description', 'auto_insights_enabled', 
        'interpretability_enabled', 'interpretability_method'
    ]
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        """Set owner and initialize default settings."""
        form.instance.owner = self.request.user
        form.instance.settings = {
            'theme': 'light',
            'refresh_interval': 300,
            'show_timestamps': True,
        }
        response = super().form_valid(form)
        
        create_notification(
            user=self.request.user,
            title='Dashboard Created',
            message=f'Dashboard "{form.instance.name}" has been created successfully.',
            notification_type='success',
            related_app='dashboards',
            related_model='Dashboard',
            related_object_id=form.instance.id
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Dashboard'
        context['button_text'] = 'Create Dashboard'
        return context


class DashboardUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = [
        'name', 'description', 'auto_insights_enabled',
        'insight_refresh_interval', 'interpretability_enabled',
        'interpretability_method'
    ]
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to update."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('dashboards:dashboard_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Dashboard'
        context['button_text'] = 'Save Changes'
        return context


class DashboardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to delete."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Delete and notify."""
        obj = self.get_object()
        dashboard_name = obj.name
        response = super().delete(request, *args, **kwargs)
        
        create_notification(
            user=request.user,
            title='Dashboard Deleted',
            message=f'Dashboard "{dashboard_name}" has been deleted.',
            notification_type='info',
            related_app='dashboards',
            related_model='Dashboard'
        )
        
        return response


class DashboardPublishView(LoginRequiredMixin, DetailView):
    """
    Publish or unpublish a dashboard.
    """
    model = Dashboard
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Toggle publish status."""
        dashboard = self.get_object()
        action = request.POST.get('action', 'publish')
        
        if action == 'publish':
            dashboard.is_published = True
        elif action == 'unpublish':
            dashboard.is_published = False
        
        dashboard.save()
        return redirect('dashboards:dashboard_detail', pk=dashboard.pk)


class DashboardLayoutView(LoginRequiredMixin, DetailView):
    """
    View and edit dashboard layout.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/layout.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Save layout configuration."""
        dashboard = self.get_object()
        try:
            layout_data = json.loads(request.body)
            dashboard.layout = layout_data
            dashboard.save()
            return JsonResponse({'success': True, 'message': 'Layout saved'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


class DashboardVisualizationView(LoginRequiredMixin, DetailView):
    """
    Manage visualizations on a dashboard.
    """
    model = Dashboard
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Add or remove visualizations."""
        dashboard = self.get_object()
        action = request.POST.get('action', 'add')
        visualization_id = request.POST.get('visualization_id')
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            
            if action == 'add':
                dashboard.visualizations.add(visualization)
                message = 'Visualization added to dashboard'
            elif action == 'remove':
                dashboard.visualizations.remove(visualization)
                message = 'Visualization removed from dashboard'
            
            return JsonResponse({'success': True, 'message': message})
        except Visualization.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Visualization not found'}, status=404)


class DashboardInsightsView(LoginRequiredMixin, ListView):
    """View all insights for a specific dashboard."""
    model = DashboardInsight
    template_name = 'dashboards/insights/list.html'
    context_object_name = 'insights'
    paginate_by = 30
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get insights for the specified dashboard."""
        dashboard_id = self.kwargs.get('pk')
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id, owner=self.request.user)
        
        queryset = DashboardInsight.objects.filter(dashboard=dashboard)
        
        # Filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', '-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = self.kwargs.get('pk')
        context['dashboard'] = get_object_or_404(Dashboard, pk=dashboard_id)
        context['categories'] = DashboardInsight.INSIGHT_CATEGORIES
        context['priorities'] = DashboardInsight.PRIORITY_LEVELS
        return context


class InsightAcknowledgeView(LoginRequiredMixin, DetailView):
    """Acknowledge a dashboard insight."""
    model = DashboardInsight
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Mark insight as acknowledged."""
        insight = self.get_object()
        
        # Verify access
        if insight.dashboard.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        insight.acknowledge()
        
        return JsonResponse({
            'success': True,
            'message': 'Insight acknowledged',
            'action_taken': insight.action_taken
        })


class InterpretabilityAnalysisView(LoginRequiredMixin, ListView):
    """View ML interpretability analyses for a dashboard."""
    model = InterpretabilityAnalysis
    template_name = 'dashboards/interpretability/list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get analyses for the specified dashboard."""
        dashboard_id = self.kwargs.get('pk')
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id, owner=self.request.user)
        return InterpretabilityAnalysis.objects.filter(dashboard=dashboard).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = self.kwargs.get('pk')
        context['dashboard'] = get_object_or_404(Dashboard, pk=dashboard_id)
        context['analysis_types'] = InterpretabilityAnalysis.ANALYSIS_TYPES
        return context


class InterpretabilityDetailView(LoginRequiredMixin, DetailView):
    """View detailed interpretability analysis results."""
    model = InterpretabilityAnalysis
    template_name = 'dashboards/interpretability/detail.html'
    context_object_name = 'analysis'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show analyses from user's dashboards."""
        return InterpretabilityAnalysis.objects.filter(dashboard__owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.get_object()
        
        # Prepare visualization data
        context['viz_data'] = json.dumps(analysis.visualization_data)
        context['top_features'] = analysis.top_features(n=15)
        
        return context


class DashboardRefreshInsightsView(LoginRequiredMixin, DetailView):
    """Manually trigger insight refresh for a dashboard."""
    model = Dashboard
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Trigger insight refresh."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Trigger refresh
        dashboard.last_insight_refresh = timezone.now()
        dashboard.save(update_fields=['last_insight_refresh'])
        
        return JsonResponse({'success': True, 'message': 'Insight refresh triggered'})


# ============================================================================
# DASHBOARD API VIEWSETS
# ============================================================================

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    DashboardSerializer, DashboardInsightSerializer, DashboardSummarySerializer,
    DashboardWidgetSerializer, InterpretabilityAnalysisSerializer, DashboardShareSerializer
)


class DashboardViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Dashboard model.
    Provides CRUD operations and intelligent dashboard management.
    """
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        """Use summary serializer for list, full for detail."""
        if self.action == 'list':
            return DashboardSummarySerializer
        return DashboardSerializer
    
    def get_queryset(self):
        """Filter dashboards - user's owned and shared ones."""
        user = self.request.user
        owned = Q(owner=user)
        shared = Q(shares__shared_with=user)
        
        return Dashboard.objects.filter(owned | shared).distinct()
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    def perform_update(self, serializer):
        """Verify ownership or edit permission on update."""
        instance = serializer.instance
        user = self.request.user
        
        if instance.owner != user:
            share = DashboardShare.objects.filter(
                dashboard=instance,
                shared_with=user
            ).first()
            
            if not share or not share.can_edit() or share.is_expired:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a dashboard (make it publicly viewable)."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can publish a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard.is_published = True
        dashboard.save()
        
        return Response({
            'status': 'dashboard published',
            'is_published': True
        })
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a dashboard."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can unpublish a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard.is_published = False
        dashboard.save()
        
        return Response({
            'status': 'dashboard unpublished',
            'is_published': False
        })
    
    @action(detail=True, methods=['post'])
    def add_visualization(self, request, pk=None):
        """Add a visualization to the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        if not visualization_id:
            return Response(
                {'error': 'visualization_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            
            if visualization.owner != request.user and not visualization.is_public:
                return Response(
                    {'error': 'You do not have access to this visualization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            dashboard.visualizations.add(visualization)
            
            return Response({
                'status': 'visualization added',
                'visualization_id': visualization_id
            })
        except Visualization.DoesNotExist:
            return Response(
                {'error': 'Visualization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_visualization(self, request, pk=None):
        """Remove a visualization from the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        if not visualization_id:
            return Response(
                {'error': 'visualization_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            dashboard.visualizations.remove(visualization)
            
            return Response({
                'status': 'visualization removed',
                'visualization_id': visualization_id
            })
        except Visualization.DoesNotExist:
            return Response(
                {'error': 'Visualization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def add_dataset(self, request, pk=None):
        """Add a dataset to monitor for insights."""
        dashboard = self.get_object()
        dataset_id = request.data.get('dataset_id')
        
        if not dataset_id:
            return Response(
                {'error': 'dataset_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from datasets.models import Dataset
        
        try:
            dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
            dashboard.datasets.add(dataset)
            
            return Response({
                'status': 'dataset added',
                'dataset_id': dataset_id
            })
        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Dataset not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_layout(self, request, pk=None):
        """Update dashboard layout configuration."""
        dashboard = self.get_object()
        layout = request.data.get('layout', {})
        
        if not isinstance(layout, dict):
            return Response(
                {'error': 'layout must be a JSON object'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dashboard.layout = layout
        dashboard.save()
        
        return Response({
            'status': 'layout updated',
            'layout': dashboard.layout
        })
    
    @action(detail=True, methods=['post'])
    def refresh_insights(self, request, pk=None):
        """Manually trigger insight refresh."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can refresh insights'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard.last_insight_refresh = timezone.now()
        dashboard.save(update_fields=['last_insight_refresh'])
        
        return Response({
            'status': 'success',
            'message': 'Insight refresh triggered',
            'last_refresh': dashboard.last_insight_refresh
        })
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get all insights for this dashboard."""
        dashboard = self.get_object()
        insights = dashboard.dashboard_insights.filter(
            Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True)
        ).order_by('-priority', '-generated_at')
        
        category = request.query_params.get('category')
        if category:
            insights = insights.filter(category=category)
        
        priority = request.query_params.get('priority')
        if priority:
            insights = insights.filter(priority=priority)
        
        serializer = DashboardInsightSerializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def interpretability(self, request, pk=None):
        """Get interpretability analyses for this dashboard."""
        dashboard = self.get_object()
        
        if not dashboard.interpretability_enabled:
            return Response({
                'error': 'Interpretability not enabled for this dashboard'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analyses = dashboard.interpretability_analyses.order_by('-created_at')
        serializer = InterpretabilityAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about user's dashboards."""
        user = request.user
        user_dashboards = Dashboard.objects.filter(owner=user)
        
        return Response({
            'total_dashboards': user_dashboards.count(),
            'published_dashboards': user_dashboards.filter(is_published=True).count(),
            'auto_insights_enabled': user_dashboards.filter(auto_insights_enabled=True).count(),
            'interpretability_enabled': user_dashboards.filter(interpretability_enabled=True).count(),
            'total_views': user_dashboards.aggregate(total=Count('view_count'))['total'] or 0,
            'shared_dashboards': DashboardShare.objects.filter(shared_with=user).count(),
        })
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share dashboard with another user."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can share a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        username = request.data.get('username')
        permission_level = request.data.get('permission_level', 'view')
        expires_at = request.data.get('expires_at')
        
        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            shared_with = User.objects.get(username=username)
            
            share, created = DashboardShare.objects.update_or_create(
                dashboard=dashboard,
                shared_with=shared_with,
                defaults={
                    'shared_by': request.user,
                    'permission_level': permission_level,
                    'expires_at': expires_at
                }
            )
            
            serializer = DashboardShareSerializer(share)
            
            return Response({
                'status': 'created' if created else 'updated',
                'share': serializer.data
            })
        
        except User.DoesNotExist:
            return Response(
                {'error': f'User "{username}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """API ViewSet for dashboard widgets."""
    
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter widgets to user's dashboards."""
        return DashboardWidget.objects.filter(
            dashboard__owner=self.request.user
        )
    
    def perform_create(self, serializer):
        """Verify dashboard ownership on widget creation."""
        dashboard = serializer.validated_data['dashboard']
        if dashboard.owner != self.request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def toggle_visibility(self, request, pk=None):
        """Toggle widget visibility."""
        widget = self.get_object()
        widget.is_visible = not widget.is_visible
        widget.save()
        
        return Response({
            'status': 'success',
            'is_visible': widget.is_visible
        })


class DashboardInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for dashboard insights (read-only)."""
    
    serializer_class = DashboardInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter insights to user's dashboards."""
        return DashboardInsight.objects.filter(
            dashboard__owner=self.request.user
        ).order_by('-priority', '-generated_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an insight."""
        insight = self.get_object()
        insight.acknowledge()
        
        serializer = self.get_serializer(insight)
        return Response({
            'status': 'acknowledged',
            'insight': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def actionable(self, request):
        """Get all actionable insights that need attention."""
        insights = self.get_queryset().filter(
            is_actionable=True,
            action_taken=False
        )
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get all critical priority insights."""
        insights = self.get_queryset().filter(priority='critical')
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data)


class InterpretabilityAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for interpretability analyses (read-only)."""
    
    serializer_class = InterpretabilityAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter analyses to user's dashboards."""
        return InterpretabilityAnalysis.objects.filter(
            dashboard__owner=self.request.user
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get analyses grouped by type."""
        analyses = self.get_queryset()
        
        grouped = {}
        for analysis in analyses:
            atype = analysis.analysis_type
            if atype not in grouped:
                grouped[atype] = []
            grouped[atype].append(self.get_serializer(analysis).data)
        
        return Response(grouped)




