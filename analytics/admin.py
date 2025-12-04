"""
Admin configuration for analytics models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Insight, Report, Trend, Anomaly, Alert, Metric, Dashboard


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    """Admin for Insight model."""
    list_display = ('title', 'insight_type_display', 'dataset', 'confidence_display', 'is_validated', 'created_at')
    list_filter = ('insight_type', 'confidence_level', 'is_validated', 'created_at', 'dataset')
    search_fields = ('title', 'description', 'dataset__name')
    readonly_fields = ('created_at', 'updated_at', 'validated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'dataset', 'owner')
        }),
        ('Insight Details', {
            'fields': ('insight_type', 'confidence_level', 'metrics', 'action_items')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validated_by', 'validated_at', 'validation_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def confidence_display(self, obj):
        """Display confidence level with color."""
        colors = {
            'low': '#fbbf24',
            'medium': '#60a5fa',
            'high': '#10b981'
        }
        color = colors.get(obj.confidence_level, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_confidence_level_display()
        )
    confidence_display.short_description = 'Confidence'
    
    def insight_type_display(self, obj):
        """Display insight type."""
        return obj.get_insight_type_display()
    insight_type_display.short_description = 'Type'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin for Report model."""
    list_display = ('title', 'report_type_display', 'dataset', 'status_display', 'insight_count', 'created_at')
    list_filter = ('report_type', 'status', 'created_at', 'dataset')
    search_fields = ('title', 'dataset__name')
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'dataset', 'owner')
        }),
        ('Report Details', {
            'fields': ('report_type', 'content', 'metadata')
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'draft': '#9ca3af',
            'generated': '#60a5fa',
            'validated': '#8b5cf6',
            'published': '#10b981',
            'archived': '#6b7280'
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def report_type_display(self, obj):
        """Display report type."""
        return obj.get_report_type_display()
    report_type_display.short_description = 'Type'
    
    def insight_count(self, obj):
        """Display number of insights in report."""
        return obj.insights.count()
    insight_count.short_description = 'Insights'


@admin.register(Trend)
class TrendAdmin(admin.ModelAdmin):
    """Admin for Trend model."""
    list_display = ('name', 'dataset', 'direction_display', 'magnitude', 'start_date', 'end_date')
    list_filter = ('direction', 'dataset', 'start_date')
    search_fields = ('name', 'description', 'dataset__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'dataset')
        }),
        ('Trend Analysis', {
            'fields': ('direction', 'magnitude', 'start_value', 'end_value', 'average_value')
        }),
        ('Time Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def direction_display(self, obj):
        """Display direction with icon."""
        icons = {
            'up': '📈',
            'down': '📉',
            'stable': '➡️',
            'volatile': '⚡'
        }
        return f"{icons.get(obj.direction, '')} {obj.get_direction_display()}"
    direction_display.short_description = 'Direction'


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    """Admin for Anomaly model."""
    list_display = ('description', 'dataset', 'severity_display', 'status_display', 'detected_at')
    list_filter = ('severity', 'status', 'detected_at', 'dataset')
    search_fields = ('description', 'dataset__name')
    readonly_fields = ('detected_at', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('description', 'dataset')
        }),
        ('Anomaly Details', {
            'fields': ('deviation_score', 'deviation_description', 'expected_value', 'actual_value')
        }),
        ('Severity & Status', {
            'fields': ('severity', 'status')
        }),
        ('Tracking', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'investigation_notes', 'resolution_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('detected_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def severity_display(self, obj):
        """Display severity with color."""
        colors = {
            'info': '#3b82f6',
            'warning': '#f59e0b',
            'critical': '#ef4444',
            'severe': '#991b1b'
        }
        color = colors.get(obj.severity, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_display.short_description = 'Severity'
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'new': '#06b6d4',
            'acknowledged': '#f59e0b',
            'investigating': '#8b5cf6',
            'resolved': '#10b981',
            'false_positive': '#6b7280'
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin for Alert model."""
    list_display = ('description', 'alert_level_display', 'status_display', 'triggered_at')
    list_filter = ('alert_level', 'status', 'triggered_at')
    search_fields = ('description', 'condition')
    readonly_fields = ('triggered_at', 'created_at', 'updated_at', 'acknowledged_at', 'resolved_at')
    fieldsets = (
        ('Alert Info', {
            'fields': ('description', 'condition', 'alert_level')
        }),
        ('Trigger Details', {
            'fields': ('triggered_by', 'trigger_data')
        }),
        ('Status', {
            'fields': ('status', 'acknowledged_at', 'resolved_at')
        }),
        ('Recipients', {
            'fields': ('recipients',)
        }),
        ('Timestamps', {
            'fields': ('triggered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('recipients',)
    
    def alert_level_display(self, obj):
        """Display alert level with color."""
        colors = {
            'low': '#3b82f6',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'critical': '#991b1b'
        }
        color = colors.get(obj.alert_level, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_alert_level_display()
        )
    alert_level_display.short_description = 'Level'
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'pending': '#06b6d4',
            'active': '#ef4444',
            'acknowledged': '#f59e0b',
            'resolved': '#10b981'
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    """Admin for Metric model."""
    list_display = ('name', 'dataset', 'current_value', 'status_display', 'is_on_target_display', 'updated_at')
    list_filter = ('status', 'dataset', 'updated_at')
    search_fields = ('name', 'description', 'dataset__name')
    readonly_fields = ('created_at', 'updated_at', 'change_percentage')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'dataset')
        }),
        ('Metric Values', {
            'fields': ('current_value', 'previous_value', 'change_percentage')
        }),
        ('Thresholds & Targets', {
            'fields': ('threshold', 'target_value', 'unit')
        }),
        ('Tracking', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'normal': '#10b981',
            'warning': '#f59e0b',
            'critical': '#ef4444'
        }
        color = colors.get(obj.status, '#gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def is_on_target_display(self, obj):
        """Display if metric is on target."""
        status = '✓' if obj.is_on_target else '✗'
        color = '#10b981' if obj.is_on_target else '#ef4444'
        return format_html(
            '<span style="color: {}; font-size: 18px;">{}</span>',
            color,
            status
        )
    is_on_target_display.short_description = 'On Target'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin for Dashboard model."""
    list_display = ('name', 'owner', 'widget_count', 'is_public_display', 'updated_at')
    list_filter = ('is_public', 'updated_at', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'widget_count')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Configuration', {
            'fields': ('layout', 'is_public')
        }),
        ('Dashboard Content', {
            'fields': ('insights', 'metrics', 'datasets'),
            'classes': ('wide',)
        }),
        ('Sharing', {
            'fields': ('shared_with',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('insights', 'metrics', 'datasets', 'shared_with')
    
    def widget_count(self, obj):
        """Display total widget count."""
        count = obj.insights.count() + obj.metrics.count() + obj.datasets.count()
        return count
    widget_count.short_description = 'Widget Count'
    
    def is_public_display(self, obj):
        """Display if dashboard is public."""
        status = '🌍' if obj.is_public else '🔒'
        return status
    is_public_display.short_description = 'Public'
