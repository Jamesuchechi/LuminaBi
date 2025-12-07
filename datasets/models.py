from django.db import models
from django.conf import settings
from django.utils import timezone
import json

# File types supported
FILE_TYPE_CHOICES = [
    ('csv', 'CSV'),
    ('excel', 'Excel (xlsx/xls)'),
    ('json', 'JSON'),
    ('pdf', 'PDF'),
    ('text', 'Text'),
    ('image', 'Image with Table'),
]

OPERATION_TYPE_CHOICES = [
    ('upload', 'File Upload'),
    ('analyze', 'Analysis'),
    ('deduplicate', 'Remove Duplicates'),
    ('fill_empty', 'Fill Empty Cells'),
    ('clean_whitespace', 'Remove Whitespace'),
    ('normalize_columns', 'Normalize Column Names'),
    ('convert_types', 'Convert Data Types'),
    ('handle_missing', 'Handle Missing Values'),
]


class Dataset(models.Model):
    """Main dataset model for uploaded files"""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datasets'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='datasets/originals/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='csv')
    file_size = models.BigIntegerField(default=0)  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analysis metadata
    row_count = models.IntegerField(null=True, blank=True)
    col_count = models.IntegerField(null=True, blank=True)
    column_names = models.JSONField(default=list, blank=True)  # List of column names
    empty_rows_count = models.IntegerField(default=0)
    empty_cols_count = models.IntegerField(default=0)
    empty_cells = models.JSONField(default=list, blank=True)  # Coordinates like ['A4', 'B9']
    duplicate_rows = models.JSONField(default=list, blank=True)  # Indices of duplicate rows
    duplicate_values = models.JSONField(default=dict, blank=True)  # Column: [values]
    summary = models.TextField(blank=True)  # AI/rule-based summary
    
    # Status
    is_analyzed = models.BooleanField(default=False)
    is_cleaned = models.BooleanField(default=False)
    analysis_metadata = models.JSONField(default=dict, blank=True)
    
    # Data quality
    data_quality_score = models.FloatField(default=0.0)  # 0-100

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner})"

    def get_display_name(self):
        """Get display name with version info"""
        return self.name or self.file.name


class DatasetVersion(models.Model):
    """Track different versions of processed datasets"""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='versions')
    file = models.FileField(upload_to='datasets/versions/')
    version_number = models.IntegerField(default=1)
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPE_CHOICES)
    operation_description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_current = models.BooleanField(default=True)
    
    # Changes made
    rows_before = models.IntegerField(null=True, blank=True)
    rows_after = models.IntegerField(null=True, blank=True)
    changes_made = models.JSONField(default=dict, blank=True)  # Details of changes

    class Meta:
        ordering = ['-version_number']
        unique_together = ('dataset', 'version_number')
        indexes = [
            models.Index(fields=['dataset', '-created_at']),
        ]

    def __str__(self):
        return f"{self.dataset.name} - v{self.version_number}"


class FileAnalysis(models.Model):
    """Detailed analysis results for a dataset"""
    dataset = models.OneToOneField(Dataset, on_delete=models.CASCADE, related_name='analysis')
    analysis_data = models.JSONField(default=dict, blank=True)
    
    # Specific analysis fields
    empty_cells_detail = models.JSONField(default=list, blank=True)  # [{'cell': 'A4', 'column': 'name', 'row': 4}]
    duplicate_rows_detail = models.JSONField(default=list, blank=True)  # [{'row_indices': [1, 5, 8], 'values': [...]}]
    column_stats = models.JSONField(default=dict, blank=True)  # Per-column statistics
    data_types = models.JSONField(default=dict, blank=True)  # Detected data types per column
    missing_values = models.JSONField(default=dict, blank=True)  # Count per column
    outliers = models.JSONField(default=list, blank=True)  # List of detected outliers
    
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis of {self.dataset.name}"


class CleaningOperation(models.Model):
    """Track cleaning operations performed on datasets"""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='cleaning_operations')
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPE_CHOICES)
    parameters = models.JSONField(default=dict, blank=True)  # Operation parameters
    result = models.JSONField(default=dict, blank=True)  # Result/status
    created_by_version = models.ForeignKey(DatasetVersion, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
        default='pending'
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset', '-created_at']),
        ]

    def __str__(self):
        return f"{self.dataset.name} - {self.operation_type}"

