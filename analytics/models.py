"""
Analytics models for LuminaBI.
Handles insights, reports, trends, and anomalies for data analysis.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import JSONField
from datasets.models import Dataset


class Insight(models.Model):
    """
    Represents data insights generated from datasets.
    Insights can be trends, correlations, anomalies, summaries, etc.
    """
    
    INSIGHT_TYPES = [
        ('trend', 'Trend Analysis'),
        ('correlation', 'Correlation'),
        ('anomaly', 'Anomaly Detection'),
        ('distribution', 'Distribution'),
        ('summary', 'Summary Statistics'),
        ('forecast', 'Forecast'),
        ('clustering', 'Clustering'),
        ('classification', 'Classification'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('low', 'Low (0-33%)'),
        ('medium', 'Medium (34-66%)'),
        ('high', 'High (67-100%)'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='insights')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_insights')
    
    # Insight details
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    
    # Analysis data
    metrics = JSONField(default=dict, help_text='Key metrics and values')
    parameters = JSONField(default=dict, help_text='Parameters used for analysis')
    
    # Confidence and validation
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS, default='medium')
    confidence_score = models.FloatField(default=0.0, help_text='0.0 to 1.0')
    
    # Validation
    is_validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_insights')
    validated_at = models.DateTimeField(blank=True, null=True)
    validation_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_insight'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset', '-created_at']),
            models.Index(fields=['insight_type', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.title} ({self.get_insight_type_display()})'
    
    @property
    def is_recent(self):
        """Check if insight was created in the last 7 days."""
        return (timezone.now() - self.created_at).days < 7
    
    @property
    def action_required(self):
        """Check if insight requires action."""
        if self.insight_type == 'anomaly' and self.confidence_score > 0.75:
            return True
        return False


class Report(models.Model):
    """
    Represents data reports generated from datasets and insights.
    Reports compile insights into comprehensive analysis documents.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('validated', 'Validated'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Analysis'),
        ('executive', 'Executive Summary'),
        ('comparative', 'Comparative Analysis'),
        ('trend', 'Trend Report'),
        ('anomaly', 'Anomaly Report'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='reports')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    insights = models.ManyToManyField(Insight, related_name='reports', blank=True)
    
    # Report details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='summary')
    
    # Report content
    content = JSONField(default=dict, help_text='Report sections and content')
    metadata = JSONField(default=dict, help_text='Report metadata')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'analytics_report'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.title}'
    
    def publish(self):
        """Publish the report."""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save()
    
    @property
    def insight_count(self):
        """Get number of insights in report."""
        return self.insights.count()


class Trend(models.Model):
    """
    Represents data trends over time.
    Tracks patterns and changes in dataset values.
    """
    
    TREND_DIRECTIONS = [
        ('up', 'Upward'),
        ('down', 'Downward'),
        ('stable', 'Stable'),
        ('volatile', 'Volatile'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='trends')
    insight = models.OneToOneField(Insight, on_delete=models.SET_NULL, null=True, blank=True, related_name='trend')
    
    # Trend details
    field_name = models.CharField(max_length=255, help_text='Dataset field being analyzed')
    direction = models.CharField(max_length=20, choices=TREND_DIRECTIONS)
    magnitude = models.FloatField(help_text='Rate of change')
    
    # Analysis
    start_value = models.FloatField()
    end_value = models.FloatField()
    average_value = models.FloatField()
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_trend'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dataset', '-created_at']),
            models.Index(fields=['direction', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.field_name} - {self.get_direction_display()}'


class Anomaly(models.Model):
    """
    Represents detected anomalies in data.
    Identifies unusual patterns or outliers.
    """
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='anomalies')
    insight = models.OneToOneField(Insight, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomaly')
    
    # Anomaly details
    description = models.TextField()
    anomaly_type = models.CharField(max_length=100)
    
    # Detection data
    detected_value = models.FloatField()
    expected_range_min = models.FloatField()
    expected_range_max = models.FloatField()
    deviation_score = models.FloatField(help_text='How far from expected range (0-1)')
    
    # Severity and status
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Investigation
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_anomalies')
    resolution_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'analytics_anomaly'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['dataset', 'status', '-detected_at']),
            models.Index(fields=['severity', '-detected_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f'{self.anomaly_type} - {self.get_severity_display()}'
    
    def acknowledge(self, user=None):
        """Mark anomaly as acknowledged."""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        if user:
            self.assigned_to = user
        self.save()
    
    def resolve(self, resolution_notes=''):
        """Mark anomaly as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.save()


class Alert(models.Model):
    """
    Represents alerts triggered by insights or anomalies.
    Notifies users of important findings.
    """
    
    ALERT_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='alerts')
    anomaly = models.ForeignKey(Anomaly, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    insight = models.ForeignKey(Insight, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    
    # Alert details
    title = models.CharField(max_length=255)
    description = models.TextField()
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVELS, default='warning')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='alerts')
    
    # Timestamps
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = JSONField(default=dict, help_text='Additional alert metadata')
    
    class Meta:
        db_table = 'analytics_alert'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['dataset', 'status', '-triggered_at']),
            models.Index(fields=['alert_level', '-triggered_at']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.get_alert_level_display()}'
    
    def acknowledge(self):
        """Mark alert as acknowledged."""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Mark alert as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()


class Metric(models.Model):
    """
    Represents key performance indicators (KPIs) for datasets.
    Tracks important metrics over time.
    """
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='metrics')
    
    # Metric details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metric_type = models.CharField(max_length=100, help_text='Type of metric (e.g., sum, average, count)')
    
    # Current value
    current_value = models.FloatField()
    target_value = models.FloatField(blank=True, null=True)
    
    # Thresholds
    warning_threshold = models.FloatField(blank=True, null=True)
    critical_threshold = models.FloatField(blank=True, null=True)
    
    # Trend
    previous_value = models.FloatField(blank=True, null=True)
    change_percentage = models.FloatField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    measured_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'analytics_metric'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['dataset', '-measured_at']),
        ]
        unique_together = ('dataset', 'name')
    
    def __str__(self):
        return f'{self.dataset.filename} - {self.name}'
    
    @property
    def status(self):
        """Get metric status based on thresholds."""
        if self.critical_threshold and self.current_value >= self.critical_threshold:
            return 'critical'
        if self.warning_threshold and self.current_value >= self.warning_threshold:
            return 'warning'
        return 'normal'
    
    @property
    def is_on_target(self):
        """Check if metric is on target."""
        if not self.target_value:
            return None
        return abs(self.current_value - self.target_value) <= (self.target_value * 0.1)


class AnalyticsDashboard(models.Model):
    """
    Represents custom analytics dashboards.
    Aggregates insights, metrics, and visualizations.
    """
    
    # Dashboard details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_dashboards')
    
    # Content
    datasets = models.ManyToManyField(Dataset, related_name='analytics_dashboards')
    insights = models.ManyToManyField(Insight, related_name='analytics_dashboards', blank=True)
    metrics = models.ManyToManyField(Metric, related_name='analytics_dashboards', blank=True)
    
    # Layout
    layout = JSONField(default=dict, help_text='Dashboard layout configuration')
    
    # Sharing
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, related_name='shared_analytics_dashboards', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_dashboard'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
            models.Index(fields=['is_public', '-updated_at']),
        ]
    
    def __str__(self):
        return f'{self.name}'
    
    @property
    def widget_count(self):
        """Get number of widgets in dashboard."""
        return len(self.layout.get('widgets', []))

