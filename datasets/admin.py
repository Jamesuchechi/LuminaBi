"""
Admin configuration for datasets application.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model."""
    
    list_display = ('name', 'owner', 'file_size_display', 'dimensions_display', 'cleaned_status', 'uploaded_at')
    list_filter = ('is_cleaned', 'uploaded_at', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('uploaded_at', 'row_count', 'col_count', 'file_info')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Files', {
            'fields': ('file', 'cleaned_file')
        }),
        ('Data Information', {
            'fields': ('row_count', 'col_count', 'file_info'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('wide',)
        }),
        ('Processing', {
            'fields': ('is_cleaned',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'uploaded_at'
    
    def file_size_display(self, obj):
        """Display file size in MB."""
        if obj.file:
            size_mb = obj.file.size / (1024 * 1024)
            return format_html(
                '<span style="background-color: #e0e7ff; color: #4f46e5; padding: 4px 8px; '
                'border-radius: 4px;">{:.2f} MB</span>',
                size_mb
            )
        return '—'
    file_size_display.short_description = 'File Size'
    
    def dimensions_display(self, obj):
        """Display dataset dimensions."""
        if obj.row_count and obj.col_count:
            return f'{obj.row_count} rows × {obj.col_count} cols'
        return '—'
    dimensions_display.short_description = 'Dimensions'
    
    def cleaned_status(self, obj):
        """Display data cleaning status."""
        if obj.is_cleaned:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Cleaned</span>'
            )
        return format_html(
            '<span style="color: #f59e0b; font-weight: bold;">Raw</span>'
        )
    cleaned_status.short_description = 'Status'
    
    def file_info(self, obj):
        """Display comprehensive file information."""
        info_lines = [
            f'Original: {obj.file.name if obj.file else "Not uploaded"}',
        ]
        if obj.cleaned_file:
            info_lines.append(f'Cleaned: {obj.cleaned_file.name}')
        if obj.row_count:
            info_lines.append(f'Rows: {obj.row_count}')
        if obj.col_count:
            info_lines.append(f'Columns: {obj.col_count}')
        return '\n'.join(info_lines)
    file_info.short_description = 'File Information'

