"""
Admin configuration for visualizations application.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Visualization


@admin.register(Visualization)
class VisualizationAdmin(admin.ModelAdmin):
    """Admin interface for Visualization model."""
    
    list_display = ('title', 'owner', 'chart_type_display', 'public_status', 'dataset_name', 'created_at')
    list_filter = ('chart_type', 'is_public', 'created_at', 'owner')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'config_preview')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'owner')
        }),
        ('Configuration', {
            'fields': ('chart_type', 'config', 'dataset')
        }),
        ('Sharing', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def chart_type_display(self, obj):
        """Display chart type with icon."""
        icons = {
            'bar': '📊',
            'line': '📈',
            'pie': '🥧',
            'scatter': '🔵',
            'heatmap': '🔥',
        }
        icon = icons.get(obj.chart_type, '📉')
        return format_html(
            '<span style="font-size: 1.2em; margin-right: 8px;">{}</span>{}',
            icon,
            obj.get_chart_type_display()
        )
    chart_type_display.short_description = 'Chart Type'
    
    def public_status(self, obj):
        """Display public/private status."""
        if obj.is_public:
            return format_html(
                '<span style="color: #3b82f6; font-weight: bold;">🌐 Public</span>'
            )
        return format_html(
            '<span style="color: #6b7280; font-weight: bold;">🔒 Private</span>'
        )
    public_status.short_description = 'Visibility'
    
    def dataset_name(self, obj):
        """Display associated dataset."""
        if obj.dataset:
            return format_html(
                '<a href="/admin/datasets/dataset/{}/change/">{}</a>',
                obj.dataset.id,
                obj.dataset.name
            )
        return '—'
    dataset_name.short_description = 'Dataset'
    
    def config_preview(self, obj):
        """Preview configuration JSON."""
        import json
        try:
            config_json = json.dumps(obj.config, indent=2) if obj.config else '{}'
            return format_html(
                '<pre style="background-color: #f3f4f6; padding: 12px; '
                'border-radius: 4px; overflow-x: auto; max-height: 300px;">{}</pre>',
                config_json
            )
        except:
            return '—'
    config_preview.short_description = 'Configuration Preview'


# Register your models here.
