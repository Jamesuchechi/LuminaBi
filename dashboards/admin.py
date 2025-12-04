"""
Admin configuration for dashboards app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Dashboard


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin interface for Dashboard model."""
    
    list_display = ('name', 'owner', 'visualization_count', 'is_published_display', 'updated_at')
    list_filter = ('is_published', 'updated_at', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'visualization_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Configuration', {
            'fields': ('layout', 'is_published')
        }),
        ('Visualizations', {
            'fields': ('visualizations',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('visualizations',)
    date_hierarchy = 'created_at'
    
    def visualization_count(self, obj):
        """Display the count of visualizations."""
        count = obj.visualizations.count()
        return format_html(
            '<span style="background-color: #e0e7ff; color: #4f46e5; padding: 4px 8px; '
            'border-radius: 4px; font-weight: 500;">{} visualization{}</span>',
            count, 's' if count != 1 else ''
        )
    visualization_count.short_description = 'Visualizations'
    
    def is_published_display(self, obj):
        """Display the publication status with color."""
        if obj.is_published:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Published</span>'
            )
        return format_html(
            '<span style="color: #9ca3af; font-weight: 500;">Draft</span>'
        )
    is_published_display.short_description = 'Status'

