from rest_framework import serializers
from .models import (
    Organization, Setting, Dashboard, DashboardWidget, DashboardInsight,
    InterpretabilityAnalysis, DashboardShare
)
from django.conf import settings
from django.contrib.auth import get_user_model


class OrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=get_user_model().objects.all(), required=False
    )

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'owner',
            'members',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'owner', 'created_at', 'updated_at']


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'site_wide', 'updated_at']
        read_only_fields = ['id', 'updated_at']


# ============================================================================
# DASHBOARD SERIALIZERS (migrated from dashboards app)
# ============================================================================

class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Serializer for dashboard widgets."""
    
    visualization_title = serializers.CharField(
        source='visualization.title',
        read_only=True
    )
    insight_title = serializers.CharField(
        source='insight.title',
        read_only=True
    )
    metric_name = serializers.CharField(
        source='metric.name',
        read_only=True
    )
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'dashboard', 'title', 'widget_type', 'config',
            'position_x', 'position_y', 'width', 'height',
            'visualization', 'visualization_title',
            'insight', 'insight_title',
            'metric', 'metric_name',
            'is_visible', 'refresh_interval',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardInsightSerializer(serializers.ModelSerializer):
    """Serializer for dashboard insights."""
    
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    
    class Meta:
        model = DashboardInsight
        fields = [
            'id', 'dashboard', 'dashboard_name',
            'title', 'description', 'category', 'priority',
            'data', 'metadata', 'confidence_score',
            'is_actionable', 'action_taken',
            'source_insight', 'source_datasets',
            'generated_at', 'expires_at', 'acknowledged_at',
            'is_expired', 'is_recent'
        ]
        read_only_fields = [
            'id', 'generated_at', 'acknowledged_at',
            'is_expired', 'is_recent'
        ]


class InterpretabilityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for interpretability analyses."""
    
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    dataset_name = serializers.CharField(source='dataset.filename', read_only=True)
    top_features = serializers.SerializerMethodField()
    
    class Meta:
        model = InterpretabilityAnalysis
        fields = [
            'id', 'dashboard', 'dashboard_name',
            'dataset', 'dataset_name',
            'analysis_type', 'title', 'description',
            'model_name', 'model_type',
            'results', 'visualization_data',
            'feature_names', 'feature_importances',
            'top_features', 'sample_size', 'computation_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_top_features(self, obj):
        """Get top 10 most important features."""
        return obj.top_features(n=10)


class DashboardShareSerializer(serializers.ModelSerializer):
    """Serializer for dashboard sharing."""
    
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    shared_with_username = serializers.CharField(
        source='shared_with.username',
        read_only=True
    )
    shared_by_username = serializers.CharField(
        source='shared_by.username',
        read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)
    can_edit_permission = serializers.BooleanField(
        source='can_edit',
        read_only=True
    )
    can_admin_permission = serializers.BooleanField(
        source='can_admin',
        read_only=True
    )
    
    class Meta:
        model = DashboardShare
        fields = [
            'id', 'dashboard', 'dashboard_name',
            'shared_with', 'shared_with_username',
            'shared_by', 'shared_by_username',
            'permission_level', 'shared_at', 'expires_at',
            'last_accessed', 'is_expired',
            'can_edit_permission', 'can_admin_permission'
        ]
        read_only_fields = [
            'id', 'shared_by', 'shared_at',
            'last_accessed', 'is_expired'
        ]


class DashboardSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for dashboard lists."""
    
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'owner', 'owner_username', 'name', 'description',
            'auto_insights_enabled', 'interpretability_enabled',
            'created_at', 'updated_at', 'is_published', 'is_template',
            'view_count', 'insight_count', 'widget_count'
        ]
        read_only_fields = [
            'id', 'owner', 'created_at', 'updated_at',
            'view_count', 'insight_count', 'widget_count'
        ]


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model with nested relationships."""
    
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    # Nested serializers for detailed view
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    dashboard_insights = DashboardInsightSerializer(
        many=True,
        read_only=True,
        source='dashboard_insights'
    )
    
    # Computed fields
    insight_count = serializers.IntegerField(read_only=True)
    widget_count = serializers.IntegerField(read_only=True)
    needs_refresh = serializers.BooleanField(
        source='needs_insight_refresh',
        read_only=True
    )
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'owner', 'owner_username', 'name', 'description',
            'layout', 'settings', 'visualizations', 'datasets',
            'auto_insights_enabled', 'insight_refresh_interval',
            'last_insight_refresh', 'interpretability_enabled',
            'interpretability_method', 'created_at', 'updated_at',
            'is_published', 'is_template', 'view_count',
            'last_viewed_at', 'widgets', 'dashboard_insights',
            'insight_count', 'widget_count', 'needs_refresh'
        ]
        read_only_fields = [
            'id', 'owner', 'created_at', 'updated_at',
            'view_count', 'last_viewed_at', 'last_insight_refresh',
            'insight_count', 'widget_count', 'needs_refresh'
        ]
