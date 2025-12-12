"""
API Views for LuminaBI.
REST API endpoints for all resources.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Q

from core.models import Organization, Setting, AuditLog
from accounts.models import UserProfile
from analytics.models import Insight, Report, Trend, Anomaly, Alert, Metric, AnalyticsDashboard
from datasets.models import Dataset
from visualizations.models import Visualization
from core.models import Dashboard as DashboardModel

from .serializers import (
    OrganizationSerializer, SettingSerializer, AuditLogSerializer,
    UserProfileSerializer, UserSerializer,
    InsightSerializer, ReportSerializer, TrendSerializer, AnomalySerializer,
    AlertSerializer, MetricSerializer, AnalyticsDashboardSerializer,
    DatasetSerializer, VisualizationSerializer, DashboardModelSerializer
)


# ============================================================================
# CUSTOM PERMISSIONS
# ============================================================================

class IsOwner(permissions.BasePermission):
    """Permission to check if user is the owner of the object."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to allow owner to edit, others read only."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


# ============================================================================
# CORE API VIEWSETS
# ============================================================================

class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization model."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
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
    """ViewSet for Setting model."""
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter settings by user's organization."""
        user_orgs = Organization.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        )
        return Setting.objects.filter(
            Q(site_wide=True) | Q(organization__in=user_orgs)
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog model (read-only)."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter audit logs by user's organizations."""
        user_orgs = Organization.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        )
        return AuditLog.objects.filter(user__organizations__in=user_orgs).distinct()


# ============================================================================
# ANALYTICS API VIEWSETS
# ============================================================================

class InsightViewSet(viewsets.ModelViewSet):
    """ViewSet for Insight model."""
    serializer_class = InsightSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter insights to user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Insight.objects.filter(dataset__in=user_datasets)
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Mark insight as validated."""
        insight = self.get_object()
        insight.is_validated = True
        insight.validated_by = request.user
        insight.validation_notes = request.data.get('notes', '')
        insight.save()
        return Response({'status': 'insight validated'})
    
    @action(detail=True, methods=['post'])
    def invalidate(self, request, pk=None):
        """Mark insight as invalid."""
        insight = self.get_object()
        insight.is_validated = False
        insight.validated_by = None
        insight.save()
        return Response({'status': 'insight invalidated'})


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Report model."""
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter reports to user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Report.objects.filter(dataset__in=user_datasets)
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a report."""
        report = self.get_object()
        report.publish()
        return Response({'status': 'report published'})


class TrendViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Trend model (read-only)."""
    serializer_class = TrendSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter trends to user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Trend.objects.filter(dataset__in=user_datasets)


class AnomalyViewSet(viewsets.ModelViewSet):
    """ViewSet for Anomaly model."""
    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-detected_at']
    
    def get_queryset(self):
        """Filter anomalies to user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Anomaly.objects.filter(dataset__in=user_datasets)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an anomaly."""
        anomaly = self.get_object()
        anomaly.acknowledge(user=request.user)
        return Response({'status': 'anomaly acknowledged'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an anomaly."""
        anomaly = self.get_object()
        resolution_notes = request.data.get('notes', '')
        anomaly.resolve(resolution_notes=resolution_notes)
        return Response({'status': 'anomaly resolved'})


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for Alert model."""
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-triggered_at']
    
    def get_queryset(self):
        """Filter alerts to current user."""
        return Alert.objects.filter(recipients=self.request.user)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        alert.acknowledge()
        return Response({'status': 'alert acknowledged'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        alert.resolve()
        return Response({'status': 'alert resolved'})


class MetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Metric model (read-only)."""
    serializer_class = MetricSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter metrics to user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Metric.objects.filter(dataset__in=user_datasets)


class AnalyticsDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for AnalyticsDashboard model."""
    serializer_class = AnalyticsDashboardSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter dashboards to user's dashboards."""
        return AnalyticsDashboard.objects.filter(
            Q(owner=self.request.user) | Q(shared_with=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share dashboard with users."""
        dashboard = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        from django.contrib.auth.models import User
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            dashboard.shared_with.add(user)
        
        return Response({'status': 'dashboard shared', 'shared_with': user_ids})
    
    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """Unshare dashboard with users."""
        dashboard = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        from django.contrib.auth.models import User
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            dashboard.shared_with.remove(user)
        
        return Response({'status': 'dashboard unshared'})


# ============================================================================
# DATASET & VISUALIZATION API VIEWSETS
# ============================================================================

class DatasetViewSet(viewsets.ModelViewSet):
    """ViewSet for Dataset model."""
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter datasets to user's datasets."""
        return Dataset.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)


class VisualizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Visualization model."""
    serializer_class = VisualizationSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter visualizations to user's visualizations."""
        return Visualization.objects.filter(
            Q(owner=self.request.user) | Q(is_public=True)
        )
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)


class DashboardModelViewSet(viewsets.ModelViewSet):
    """ViewSet for Dashboard model in dashboards app."""
    serializer_class = DashboardModelSerializer
    permission_classes = [IsAuthenticated]
    queryset = DashboardModel.objects.all()
    ordering = ['-updated_at']
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)


# ============================================================================
# UTILITY API ENDPOINTS
# ============================================================================

def health_check(request):
    """Simple health check for the API."""
    return JsonResponse({
        "status": "ok",
        "service": "LuminaBI API",
        "version": "1.0"
    })


def api_root(request):
    """API root information."""
    return JsonResponse({
        "service": "LuminaBI REST API",
        "version": "1.0",
        "endpoints": {
            "auth": "/api-token-auth/",
            "token": "/api/token/",
            "token_refresh": "/api/token/refresh/",
            "health": "/api/health/",
            "resources": {
                "organizations": "/api/organizations/",
                "settings": "/api/settings/",
                "audit_logs": "/api/audit-logs/",
                "insights": "/api/insights/",
                "reports": "/api/reports/",
                "trends": "/api/trends/",
                "anomalies": "/api/anomalies/",
                "alerts": "/api/alerts/",
                "metrics": "/api/metrics/",
                "dashboards": "/api/dashboards/",
                "datasets": "/api/datasets/",
                "visualizations": "/api/visualizations/",
            }
        }
    })
