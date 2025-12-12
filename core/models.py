from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import JSONField


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_organizations'
    )
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='organizations', blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'org'
            slug = base
            suffix = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{suffix}"
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Setting(models.Model):
    key = models.CharField(max_length=128, unique=True)
    value = models.JSONField(default=dict, blank=True)
    site_wide = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class AuditLog(models.Model):
    action = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"


class Notification(models.Model):
    """Model for user notifications."""
    TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default='info')
    
    # Link related fields
    related_app = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'datasets', 'dashboards'
    related_model = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'Dataset', 'Dashboard'
    related_object_id = models.IntegerField(blank=True, null=True)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ============================================================================
# DASHBOARD MODELS (migrated from dashboards app)
# ============================================================================

class Dashboard(models.Model):
    """
    Enhanced Dashboard with automatic insights and ML interpretability.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboards'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Layout and configuration
    layout = JSONField(default=dict, blank=True, help_text='Grid/widget layout configuration')
    settings = JSONField(default=dict, blank=True, help_text='Dashboard settings and preferences')
    
    # Relationships
    visualizations = models.ManyToManyField(
        'visualizations.Visualization', 
        blank=True, 
        related_name='dashboards'
    )
    datasets = models.ManyToManyField(
        'datasets.Dataset',
        blank=True,
        related_name='dashboards',
        help_text='Datasets to monitor for insights'
    )
    
    # Auto-insights configuration
    auto_insights_enabled = models.BooleanField(
        default=True,
        help_text='Enable automatic insight generation'
    )
    insight_refresh_interval = models.IntegerField(
        default=3600,
        help_text='Insight refresh interval in seconds (default: 1 hour)'
    )
    last_insight_refresh = models.DateTimeField(null=True, blank=True)
    
    # ML Interpretability settings
    interpretability_enabled = models.BooleanField(
        default=False,
        help_text='Enable SHAP/LIME analysis for predictions'
    )
    interpretability_method = models.CharField(
        max_length=20,
        choices=[
            ('shap', 'SHAP'),
            ('lime', 'LIME'),
            ('both', 'Both SHAP and LIME'),
        ],
        default='shap',
        blank=True
    )
    
    # Status and metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    is_template = models.BooleanField(
        default=False,
        help_text='Mark as template for creating new dashboards'
    )
    
    # Performance tracking
    view_count = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
            models.Index(fields=['is_published', '-updated_at']),
            models.Index(fields=['is_template']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def scheduled_report_enabled(self):
        """Check if scheduled reports are enabled."""
        return self.settings.get('scheduled_report_enabled', False)
    
    def get_scheduled_report_frequency(self):
        """Get scheduled report frequency."""
        return self.settings.get('scheduled_report_frequency', 'daily')
    
    def get_scheduled_report_recipients(self):
        """Get scheduled report recipients."""
        return self.settings.get('scheduled_report_recipients', [])
    
    def needs_insight_refresh(self):
        """Check if insights need refreshing."""
        if not self.auto_insights_enabled:
            return False
        if not self.last_insight_refresh:
            return True
        elapsed = (timezone.now() - self.last_insight_refresh).total_seconds()
        return elapsed >= self.insight_refresh_interval
    
    def increment_view_count(self):
        """Increment view count and update last viewed timestamp."""
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])
    
    @property
    def insight_count(self):
        """Get total number of insights."""
        return self.dashboard_insights.count()
    
    @property
    def widget_count(self):
        """Get number of widgets in dashboard."""
        return len(self.layout.get('widgets', []))


class DashboardWidget(models.Model):
    """
    Individual widget on a dashboard.
    Can display insights, visualizations, metrics, or custom content.
    """
    WIDGET_TYPES = [
        ('insight', 'Insight Card'),
        ('visualization', 'Visualization'),
        ('metric', 'Metric Display'),
        ('anomaly', 'Anomaly Alert'),
        ('trend', 'Trend Chart'),
        ('table', 'Data Table'),
        ('text', 'Text/Markdown'),
        ('iframe', 'Embedded Content'),
        ('interpretability', 'ML Interpretability'),
    ]
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    
    # Widget configuration
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    config = JSONField(default=dict, help_text='Widget-specific configuration')
    
    # Layout
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4)
    height = models.IntegerField(default=3)
    
    # Content references
    visualization = models.ForeignKey(
        'visualizations.Visualization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_widgets'
    )
    insight = models.ForeignKey(
        'analytics.Insight',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_widgets'
    )
    metric = models.ForeignKey(
        'analytics.Metric',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_widgets'
    )
    
    # Display settings
    is_visible = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(
        default=0,
        help_text='Auto-refresh interval in seconds (0 = no refresh)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position_y', 'position_x']
        indexes = [
            models.Index(fields=['dashboard', 'widget_type']),
            models.Index(fields=['dashboard', 'position_y', 'position_x']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.widget_type})"


class DashboardInsight(models.Model):
    """
    Auto-generated insights specific to a dashboard.
    Aggregates and summarizes data across multiple datasets.
    """
    INSIGHT_CATEGORIES = [
        ('summary', 'Summary Statistics'),
        ('trend', 'Trend Analysis'),
        ('anomaly', 'Anomaly Detection'),
        ('correlation', 'Correlation Analysis'),
        ('prediction', 'Predictive Insights'),
        ('performance', 'Performance Metrics'),
        ('alert', 'Alert/Warning'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='dashboard_insights'
    )
    
    # Insight content
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=INSIGHT_CATEGORIES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Data
    data = JSONField(default=dict, help_text='Insight data and metrics')
    metadata = JSONField(default=dict, help_text='Additional metadata')
    
    # Confidence and validation
    confidence_score = models.FloatField(
        default=0.0,
        help_text='Confidence score (0.0 to 1.0)'
    )
    is_actionable = models.BooleanField(
        default=False,
        help_text='Requires user action'
    )
    action_taken = models.BooleanField(default=False)
    
    # Source tracking
    source_insight = models.ForeignKey(
        'analytics.Insight',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_insights'
    )
    source_datasets = models.ManyToManyField(
        'datasets.Dataset',
        blank=True,
        related_name='dashboard_insights'
    )
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this insight becomes stale'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-generated_at']
        indexes = [
            models.Index(fields=['dashboard', '-generated_at']),
            models.Index(fields=['dashboard', 'priority', '-generated_at']),
            models.Index(fields=['category', '-generated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.category})"
    
    def acknowledge(self):
        """Mark insight as acknowledged."""
        self.acknowledged_at = timezone.now()
        if self.is_actionable:
            self.action_taken = True
        self.save()
    
    @property
    def is_expired(self):
        """Check if insight has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_recent(self):
        """Check if insight was generated recently (within 24 hours)."""
        return (timezone.now() - self.generated_at).total_seconds() < 86400


class InterpretabilityAnalysis(models.Model):
    """
    Stores ML model interpretability analysis (SHAP, LIME, etc.)
    for predictions shown on dashboards.
    """
    ANALYSIS_TYPES = [
        ('shap_values', 'SHAP Values'),
        ('shap_summary', 'SHAP Summary Plot'),
        ('shap_dependence', 'SHAP Dependence Plot'),
        ('lime_explanation', 'LIME Explanation'),
        ('feature_importance', 'Feature Importance'),
        ('partial_dependence', 'Partial Dependence'),
    ]
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='interpretability_analyses'
    )
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='interpretability_analyses'
    )
    
    # Analysis details
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Model information
    model_name = models.CharField(max_length=255, blank=True)
    model_type = models.CharField(max_length=100, blank=True)
    
    # Results
    results = JSONField(default=dict, help_text='Analysis results and data')
    visualization_data = JSONField(
        default=dict,
        help_text='Data for visualizing interpretability results'
    )
    
    # Feature information
    feature_names = JSONField(default=list, help_text='List of feature names')
    feature_importances = JSONField(default=dict, help_text='Feature importance scores')
    
    # Metadata
    sample_size = models.IntegerField(
        default=0,
        help_text='Number of samples analyzed'
    )
    computation_time = models.FloatField(
        default=0.0,
        help_text='Time taken to compute (seconds)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Interpretability analyses'
        indexes = [
            models.Index(fields=['dashboard', 'analysis_type', '-created_at']),
            models.Index(fields=['dataset', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.analysis_type})"
    
    @property
    def top_features(self, n=10):
        """Get top N most important features."""
        if not self.feature_importances:
            return []
        sorted_features = sorted(
            self.feature_importances.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return sorted_features[:n]


class DashboardShare(models.Model):
    """
    Manages dashboard sharing with other users.
    """
    PERMISSION_LEVELS = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('admin', 'Admin'),
    ]
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_dashboards'
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboards_shared_by_me'
    )
    
    # Permissions
    permission_level = models.CharField(
        max_length=10,
        choices=PERMISSION_LEVELS,
        default='view'
    )
    
    # Timestamps
    shared_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('dashboard', 'shared_with')
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['shared_with', '-shared_at']),
            models.Index(fields=['dashboard', 'permission_level']),
        ]
    
    def __str__(self):
        return f"{self.dashboard.name} shared with {self.shared_with.username}"
    
    @property
    def is_expired(self):
        """Check if share has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def can_edit(self):
        """Check if user has edit permissions."""
        return self.permission_level in ['edit', 'admin']
    
    def can_admin(self):
        """Check if user has admin permissions."""
        return self.permission_level == 'admin'


