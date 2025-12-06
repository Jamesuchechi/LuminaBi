"""
Class-based views for LuminaBI core application.
Handles organizations, settings, audit logs, and system configuration.
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

from .models import Organization, Setting, AuditLog, Notification
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
        from analytics.models import Insight, Anomaly, Alert, Trend, Metric
        from visualizations.models import Visualization
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User's datasets
        user_datasets = Dataset.objects.filter(owner=user)
        context['user_organizations'] = Organization.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()
        
        # ======= LIVE STATISTICS =======
        context['total_datasets'] = user_datasets.count()
        context['cleaned_datasets'] = user_datasets.filter(is_cleaned=True).count()
        
        # Get visualizations
        try:
            context['total_visualizations'] = Visualization.objects.filter(
                dataset__owner=user
            ).count()
        except:
            context['total_visualizations'] = 0
        
        # Get insights
        try:
            user_insights = Insight.objects.filter(dataset__owner=user)
            context['total_insights'] = user_insights.count()
            context['recent_insights'] = user_insights.order_by('-created_at')[:5]
        except:
            context['total_insights'] = 0
            context['recent_insights'] = []
        
        # Get anomalies
        try:
            user_anomalies = Anomaly.objects.filter(dataset__owner=user)
            context['total_anomalies'] = user_anomalies.count()
            context['active_anomalies'] = user_anomalies.exclude(
                status='resolved'
            ).count()
            context['critical_anomalies'] = user_anomalies.filter(
                severity='critical',
                status__in=['new', 'acknowledged']
            )[:3]
        except:
            context['total_anomalies'] = 0
            context['active_anomalies'] = 0
            context['critical_anomalies'] = []
        
        # Get alerts
        try:
            user_alerts = Alert.objects.filter(dataset__owner=user)
            context['active_alerts'] = user_alerts.filter(status='active').count()
            context['recent_alerts'] = user_alerts.order_by('-triggered_at')[:5]
        except:
            context['active_alerts'] = 0
            context['recent_alerts'] = []
        
        # Get metrics
        try:
            context['total_metrics'] = Metric.objects.filter(
                dataset__owner=user
            ).count()
        except:
            context['total_metrics'] = 0
        
        # ======= DATA HEALTH & CLEANUP =======
        if context['total_datasets'] > 0:
            context['cleaning_progress'] = int(
                (context['cleaned_datasets'] / context['total_datasets']) * 100
            )
        else:
            context['cleaning_progress'] = 0
        
        # ======= ACTIVITY STREAMS =======
        # Recent datasets
        context['recent_datasets'] = user_datasets.order_by('-uploaded_at')[:5]
        
        # Trends
        try:
            context['recent_trends'] = Trend.objects.filter(
                dataset__owner=user
            ).order_by('-created_at')[:5]
        except:
            context['recent_trends'] = []
        
        # ======= CHART DATA (JSON) =======
        # Datasets upload timeline (last 30 days)
        last_30_days = timezone.now() - timedelta(days=30)
        datasets_by_day = {}
        for dataset in user_datasets.filter(uploaded_at__gte=last_30_days):
            day = dataset.uploaded_at.strftime('%Y-%m-%d')
            datasets_by_day[day] = datasets_by_day.get(day, 0) + 1
        
        context['datasets_chart_labels'] = sorted(datasets_by_day.keys())
        context['datasets_chart_data'] = [
            datasets_by_day.get(label, 0) for label in context['datasets_chart_labels']
        ]
        
        # Insights distribution by type
        try:
            insights_by_type = user_insights.values('insight_type').annotate(
                count=Count('id')
            ).order_by('-count')
            context['insights_types'] = [item['insight_type'] for item in insights_by_type]
            context['insights_counts'] = [item['count'] for item in insights_by_type]
        except:
            context['insights_types'] = []
            context['insights_counts'] = []
        
        # Anomalies by severity
        try:
            anomalies_by_severity = user_anomalies.values('severity').annotate(
                count=Count('id')
            )
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            anomalies_by_severity = sorted(
                anomalies_by_severity, 
                key=lambda x: severity_order.get(x['severity'], 99)
            )
            context['anomaly_severities'] = [
                item['severity'].upper() for item in anomalies_by_severity
            ]
            context['anomaly_counts'] = [item['count'] for item in anomalies_by_severity]
        except:
            context['anomaly_severities'] = []
            context['anomaly_counts'] = []
        
        # System stats if admin
        if user.is_staff:
            context['total_organizations'] = Organization.objects.count()
            context['total_system_datasets'] = Dataset.objects.count()
            context['total_system_users'] = User.objects.count()
        
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




