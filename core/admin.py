from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Organization, Setting, Dashboard, DashboardWidget, DashboardInsight,
    InterpretabilityAnalysis, DashboardShare
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'site_wide', 'updated_at')
    search_fields = ('key',)


# ============================================================================
# DASHBOARD ADMIN (migrated from dashboards app)
# ============================================================================

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin interface for Dashboard model."""
    
    list_display = [
        'name', 'owner', 'is_published', 'auto_insights_enabled',
        'interpretability_enabled', 'view_count', 'created_at'
    ]
    list_filter = [
        'is_published', 'is_template', 'auto_insights_enabled',
        'interpretability_enabled', 'created_at'
    ]
    search_fields = ['name', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'last_viewed_at']
    filter_horizontal = ['visualizations', 'datasets']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'description')
        }),
        ('Configuration', {
            'fields': (
                'auto_insights_enabled', 'insight_refresh_interval',
                'interpretability_enabled', 'interpretability_method'
            )
        }),
        ('Content', {
            'fields': ('visualizations', 'datasets', 'layout', 'settings')
        }),
        ('Status', {
            'fields': (
                'is_published', 'is_template', 'view_count',
                'last_viewed_at', 'last_insight_refresh'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('owner')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Admin interface for DashboardWidget model."""
    
    list_display = [
        'title', 'dashboard', 'widget_type', 'is_visible',
        'position_display', 'size_display', 'created_at'
    ]
    list_filter = ['widget_type', 'is_visible', 'created_at']
    search_fields = ['title', 'dashboard__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('dashboard', 'title', 'widget_type', 'config')
        }),
        ('Layout', {
            'fields': (
                'position_x', 'position_y', 'width', 'height',
                'is_visible', 'refresh_interval'
            )
        }),
        ('Content References', {
            'fields': ('visualization', 'insight', 'metric'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def position_display(self, obj):
        """Display position as (x, y)."""
        return f"({obj.position_x}, {obj.position_y})"
    position_display.short_description = 'Position'
    
    def size_display(self, obj):
        """Display size as width x height."""
        return f"{obj.width} × {obj.height}"
    size_display.short_description = 'Size'


@admin.register(DashboardInsight)
class DashboardInsightAdmin(admin.ModelAdmin):
    """Admin interface for DashboardInsight model."""
    
    list_display = [
        'title', 'dashboard', 'category', 'priority_badge',
        'confidence_score', 'is_actionable', 'action_taken',
        'generated_at'
    ]
    list_filter = [
        'category', 'priority', 'is_actionable', 'action_taken',
        'generated_at'
    ]
    search_fields = ['title', 'description', 'dashboard__name']
    readonly_fields = ['generated_at', 'acknowledged_at', 'is_expired', 'is_recent']
    filter_horizontal = ['source_datasets']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('dashboard', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'confidence_score')
        }),
        ('Action', {
            'fields': ('is_actionable', 'action_taken', 'acknowledged_at')
        }),
        ('Data', {
            'fields': ('data', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Source', {
            'fields': ('source_insight', 'source_datasets'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('generated_at', 'expires_at', 'is_expired', 'is_recent')
        }),
    )
    
    def priority_badge(self, obj):
        """Display priority with colored badge."""
        colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('dashboard', 'source_insight')


@admin.register(InterpretabilityAnalysis)
class InterpretabilityAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for InterpretabilityAnalysis model."""
    
    list_display = [
        'title', 'dashboard', 'dataset', 'analysis_type',
        'model_name', 'sample_size', 'computation_time_display',
        'created_at'
    ]
    list_filter = ['analysis_type', 'model_type', 'created_at']
    search_fields = [
        'title', 'description', 'model_name',
        'dashboard__name', 'dataset__filename'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('dashboard', 'dataset', 'analysis_type', 'title', 'description')
        }),
        ('Model Information', {
            'fields': ('model_name', 'model_type')
        }),
        ('Results', {
            'fields': (
                'results', 'visualization_data',
                'feature_names', 'feature_importances'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sample_size', 'computation_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def computation_time_display(self, obj):
        """Display computation time in readable format."""
        if obj.computation_time < 1:
            return f"{obj.computation_time * 1000:.0f} ms"
        return f"{obj.computation_time:.2f} s"
    computation_time_display.short_description = 'Computation Time'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('dashboard', 'dataset')


@admin.register(DashboardShare)
class DashboardShareAdmin(admin.ModelAdmin):
    """Admin interface for DashboardShare model."""
    
    list_display = [
        'dashboard', 'shared_with', 'shared_by',
        'permission_level', 'status_badge',
        'shared_at', 'expires_at'
    ]
    list_filter = ['permission_level', 'shared_at', 'expires_at']
    search_fields = [
        'dashboard__name', 'shared_with__username', 'shared_by__username'
    ]
    readonly_fields = ['shared_at', 'last_accessed', 'is_expired']
    
    fieldsets = (
        ('Share Information', {
            'fields': (
                'dashboard', 'shared_with', 'shared_by', 'permission_level'
            )
        }),
        ('Timing', {
            'fields': ('shared_at', 'expires_at', 'last_accessed', 'is_expired')
        }),
    )
    
    def status_badge(self, obj):
        """Display share status with badge."""
        if obj.is_expired:
            return format_html(
                '<span style="background-color: red; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Expired</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Active</span>'
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('dashboard', 'shared_with', 'shared_by')
