"""
Insights models for detailed data analysis using SHAP/LIME
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField


class DataInsight(models.Model):
    """
    Represents an insight generated from a dataset.
    Includes SHAP/LIME explanations, anomalies, patterns, and relationships.
    """
    INSIGHT_TYPES = [
        ('relationship', 'Relationship'),
        ('anomaly', 'Anomaly'),
        ('pattern', 'Pattern'),
        ('outlier', 'Outlier'),
        ('correlation', 'Correlation'),
        ('distribution', 'Distribution'),
        ('trend', 'Trend'),
        ('summary', 'Summary Statistics'),
    ]
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insights'
    )
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='data_insights'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    
    # Analysis data
    analysis_data = JSONField(default=dict, help_text='Complete analysis data including SHAP values')
    confidence_score = models.FloatField(default=0.0, help_text='Confidence 0-1')
    key_features = JSONField(default=list, help_text='Most important features for this insight')
    
    # Explanation
    shap_values = JSONField(default=dict, blank=True, help_text='SHAP explanation values')
    lime_explanation = JSONField(default=dict, blank=True, help_text='LIME local explanation')
    human_explanation = models.TextField(blank=True, help_text='Human-readable explanation')
    
    # Visibility
    is_public = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['dataset', 'insight_type']),
        ]
    
    def __str__(self):
        return f"{self.get_insight_type_display()}: {self.title}"


class AnomalyDetection(models.Model):
    """
    Detected anomalies in dataset using statistical methods and ML
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    insight = models.OneToOneField(
        DataInsight,
        on_delete=models.CASCADE,
        related_name='anomaly_detection',
        null=True,
        blank=True
    )
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='anomaly_detections'
    )
    
    anomaly_type = models.CharField(max_length=50)  # e.g., 'outlier', 'sudden_change', 'drift'
    affected_columns = JSONField(default=list)
    affected_rows = JSONField(default=list)
    
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    anomaly_score = models.FloatField()  # 0-1 score
    
    details = JSONField(default=dict)
    visualization_data = JSONField(default=dict, help_text='Data for visualizing anomalies')
    
    detected_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-anomaly_score', '-detected_at']
    
    def __str__(self):
        return f"{self.anomaly_type} - {self.dataset.name}"


class OutlierAnalysis(models.Model):
    """
    Identifies and analyzes outliers in datasets
    """
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='outlier_analyses'
    )
    
    column = models.CharField(max_length=255)
    method = models.CharField(
        max_length=50,
        choices=[
            ('iqr', 'Interquartile Range'),
            ('zscore', 'Z-Score'),
            ('isolation_forest', 'Isolation Forest'),
            ('lof', 'Local Outlier Factor'),
        ]
    )
    
    outlier_indices = JSONField(default=list)
    outlier_values = JSONField(default=list)
    outlier_count = models.IntegerField()
    outlier_percentage = models.FloatField()
    
    threshold_values = JSONField(default=dict, help_text='Method-specific thresholds')
    statistics = JSONField(default=dict, help_text='Statistical summary')
    
    visualization_data = JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('dataset', 'column', 'method')
    
    def __str__(self):
        return f"Outliers in {self.dataset.name}::{self.column}"


class RelationshipAnalysis(models.Model):
    """
    Analyzes relationships and correlations between columns
    """
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='relationship_analyses'
    )
    
    feature_1 = models.CharField(max_length=255)
    feature_2 = models.CharField(max_length=255)
    
    correlation_coefficient = models.FloatField()
    p_value = models.FloatField(null=True, blank=True)
    is_significant = models.BooleanField(default=False)
    
    relationship_type = models.CharField(
        max_length=50,
        choices=[
            ('linear', 'Linear'),
            ('non_linear', 'Non-Linear'),
            ('inverse', 'Inverse'),
            ('no_relationship', 'No Relationship'),
        ]
    )
    
    visualization_data = JSONField(default=dict)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.feature_1} <-> {self.feature_2}"


class ModelExplanation(models.Model):
    """
    SHAP/LIME explanations for ML predictions or patterns
    """
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='model_explanations'
    )
    
    model_type = models.CharField(max_length=100)  # e.g., 'random_forest', 'xgboost'
    target_variable = models.CharField(max_length=255, blank=True)
    
    # Global explanations
    shap_summary = JSONField(default=dict, help_text='SHAP summary statistics')
    feature_importance = JSONField(default=dict, help_text='Feature importance ranking')
    
    # Local explanations
    sample_explanations = JSONField(default=list, help_text='LIME explanations for samples')
    
    # Visualization
    summary_plot_data = JSONField(default=dict)
    force_plot_data = JSONField(default=dict)
    dependence_plot_data = JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.model_type} - {self.dataset.name}"


class InsightReport(models.Model):
    """
    Comprehensive report combining multiple insights
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insight_reports'
    )
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='insight_reports'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Component insights
    insights = models.ManyToManyField(DataInsight, related_name='reports', blank=True)
    anomalies = models.ManyToManyField(AnomalyDetection, related_name='reports', blank=True)
    outlier_analyses = models.ManyToManyField(OutlierAnalysis, related_name='reports', blank=True)
    relationships = models.ManyToManyField(RelationshipAnalysis, related_name='reports', blank=True)
    
    # Report data
    summary = JSONField(default=dict, help_text='Executive summary')
    key_findings = JSONField(default=list)
    recommendations = JSONField(default=list)
    
    # Meta
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report: {self.title}"
