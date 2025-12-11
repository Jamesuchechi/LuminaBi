"""
API Serializers for LuminaBI.
REST API serializers for all models.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import Organization, Setting, AuditLog
from accounts.models import UserProfile
from analytics.models import Insight, Report, Trend, Anomaly, Alert, Metric, AnalyticsDashboard
from datasets.models import Dataset
from visualizations.models import Visualization
from dashboards.models import Dashboard as DashboardModel


# ============================================================================
# CORE SERIALIZERS
# ============================================================================

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'description', 'owner', 'members_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'members_count']


class SettingSerializer(serializers.ModelSerializer):
    """Serializer for Setting model."""
    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'data_type', 'site_wide', 'organization', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'content_type', 'object_id', 'changes', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']


# ============================================================================
# ACCOUNTS SERIALIZERS
# ============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'email', 'role', 'organization', 'notification_preferences', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'profile', 'date_joined']
        read_only_fields = ['id', 'date_joined']


# ============================================================================
# ANALYTICS SERIALIZERS
# ============================================================================

class InsightSerializer(serializers.ModelSerializer):
    """Serializer for Insight model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Insight
        fields = ['id', 'title', 'description', 'dataset', 'dataset_name', 'owner', 'owner_name', 
                  'insight_type', 'confidence_level', 'metrics', 'action_items', 'is_validated', 
                  'validated_by', 'validated_at', 'validation_notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'validated_at']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    insight_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'title', 'description', 'dataset', 'dataset_name', 'owner', 'owner_name',
                  'report_type', 'status', 'content', 'metadata', 'insight_count', 'published_at',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at']
    
    def get_insight_count(self, obj):
        return obj.insights.count()


class TrendSerializer(serializers.ModelSerializer):
    """Serializer for Trend model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = Trend
        fields = ['id', 'name', 'description', 'dataset', 'dataset_name', 'direction', 'magnitude',
                  'start_value', 'end_value', 'average_value', 'start_date', 'end_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnomalySerializer(serializers.ModelSerializer):
    """Serializer for Anomaly model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = Anomaly
        fields = ['id', 'description', 'dataset', 'dataset_name', 'severity', 'status', 'deviation_score',
                  'deviation_description', 'expected_value', 'actual_value', 'detected_at', 'acknowledged_by',
                  'acknowledged_at', 'investigation_notes', 'resolution_notes', 'resolved_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'detected_at', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""
    triggered_by_name = serializers.CharField(source='triggered_by.username', read_only=True)
    
    class Meta:
        model = Alert
        fields = ['id', 'description', 'condition', 'alert_level', 'status', 'triggered_by', 'triggered_by_name',
                  'trigger_data', 'triggered_at', 'acknowledged_at', 'resolved_at', 'recipients', 'created_at', 'updated_at']
        read_only_fields = ['id', 'triggered_at', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at']


class MetricSerializer(serializers.ModelSerializer):
    """Serializer for Metric model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = Metric
        fields = ['id', 'name', 'description', 'dataset', 'dataset_name', 'current_value', 'previous_value',
                  'change_percentage', 'threshold', 'target_value', 'unit', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'change_percentage']


class AnalyticsDashboardSerializer(serializers.ModelSerializer):
    """Serializer for AnalyticsDashboard model."""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    widget_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalyticsDashboard
        fields = ['id', 'name', 'description', 'owner', 'owner_name', 'layout', 'is_public', 'widget_count',
                  'insights', 'metrics', 'datasets', 'shared_with', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_widget_count(self, obj):
        return obj.insights.count() + obj.metrics.count() + obj.datasets.count()


# ============================================================================
# DATASET & VISUALIZATION SERIALIZERS
# ============================================================================

class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for Dataset model."""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'description', 'owner', 'owner_name', 'file_type',
                  'row_count', 'col_count', 'column_names', 'is_analyzed', 'data_quality_score',
                  'uploaded_at', 'updated_at']
        read_only_fields = ['id', 'row_count', 'col_count', 'uploaded_at', 'updated_at']


class VisualizationSerializer(serializers.ModelSerializer):
    """Serializer for Visualization model."""
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Visualization
        fields = ['id', 'title', 'description', 'dataset', 'dataset_name', 'owner', 'owner_name',
              'chart_type', 'config', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'owner_name', 'dataset_name', 'created_at', 'updated_at']


class DashboardModelSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model in dashboards app."""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = DashboardModel
        fields = ['id', 'title', 'description', 'owner', 'owner_name', 'layout',
                  'visualizations', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
