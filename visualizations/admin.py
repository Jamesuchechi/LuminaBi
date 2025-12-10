"""
Admin configuration for visualizations application.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Visualization, VisualizationAccessLog, VisualizationTag, VisualizationComment, VisualizationFavorite


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
            'area': '📉',
            'radar': '🎯',
            'bubble': '🫧',
            'donut': '🍩',
            'treemap': '🌳',
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

class VisualizationAccessLogAdmin(admin.ModelAdmin):
    """Admin interface for VisualizationAccessLog model."""
    
    list_display = ('visualization', 'user_display', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at', 'visualization__owner')
    search_fields = ('visualization__title', 'user__username', 'ip_address')
    date_hierarchy = 'accessed_at'
    
    def user_display(self, obj):
        """Display user or anonymous."""
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return 'Anonymous'
    user_display.short_description = 'User'
    
class VisualizationTagAdmin(admin.ModelAdmin):
    """Admin interface for VisualizationTag model."""
    
    list_display = ('name', 'visualization_link')
    search_fields = ('name', 'visualization__title')
    
    def visualization_link(self, obj):
        """Link to associated visualization."""
        return format_html(
            '<a href="/admin/visualizations/visualization/{}/change/">{}</a>',
            obj.visualization.id,
            obj.visualization.title
        )
    visualization_link.short_description = 'Visualization'
    
class VisualizationCommentAdmin(admin.ModelAdmin):
    """Admin interface for VisualizationComment model."""
    
    list_display = ('visualization_link', 'user_link', 'created_at', 'short_content')
    list_filter = ('created_at', 'visualization__owner')
    search_fields = ('visualization__title', 'user__username', 'content')
    date_hierarchy = 'created_at'
    
    def visualization_link(self, obj):
        """Link to associated visualization."""
        return format_html(
            '<a href="/admin/visualizations/visualization/{}/change/">{}</a>',
            obj.visualization.id,
            obj.visualization.title
        )
    visualization_link.short_description = 'Visualization'
    
    def user_link(self, obj):
        """Link to commenting user."""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'
    
    def short_content(self, obj):
        """Short preview of comment content."""
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Comment Preview'
    
class VisualizationFavoriteAdmin(admin.ModelAdmin):
    """Admin interface for VisualizationFavorite model."""
    
    list_display = ('visualization_link', 'user_link')
    search_fields = ('visualization__title', 'user__username')
    
    def visualization_link(self, obj):
        """Link to associated visualization."""
        return format_html(
            '<a href="/admin/visualizations/visualization/{}/change/">{}</a>',
            obj.visualization.id,
            obj.visualization.title
        )
    visualization_link.short_description = 'Visualization'
    
    def user_link(self, obj):
        """Link to favoriting user."""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'


# Register all admin models
admin.site.register(VisualizationAccessLog, VisualizationAccessLogAdmin)
admin.site.register(VisualizationTag, VisualizationTagAdmin)
admin.site.register(VisualizationComment, VisualizationCommentAdmin)
admin.site.register(VisualizationFavorite, VisualizationFavoriteAdmin)
