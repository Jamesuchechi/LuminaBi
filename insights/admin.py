"""
Admin configuration for insights app
"""

from django.contrib import admin
from .models import (
    DataInsight, AnomalyDetection, OutlierAnalysis, 
    RelationshipAnalysis, ModelExplanation, InsightReport
)


@admin.register(DataInsight)
class DataInsightAdmin(admin.ModelAdmin):
    list_display = ('title', 'insight_type', 'dataset', 'owner', 'confidence_score', 'created_at')
    list_filter = ('insight_type', 'is_public', 'is_pinned', 'created_at')
    search_fields = ('title', 'description', 'dataset__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'dataset', 'title', 'description', 'insight_type')
        }),
        ('Analysis', {
            'fields': ('analysis_data', 'confidence_score', 'key_features')
        }),
        ('Explanations', {
            'fields': ('shap_values', 'lime_explanation', 'human_explanation'),
            'classes': ('collapse',)
        }),
        ('Visibility', {
            'fields': ('is_public', 'is_pinned')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ('anomaly_type', 'dataset', 'severity', 'anomaly_score', 'detected_at', 'acknowledged')
    list_filter = ('severity', 'anomaly_type', 'detected_at', 'acknowledged')
    search_fields = ('anomaly_type', 'dataset__name')
    readonly_fields = ('detected_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('insight', 'dataset', 'anomaly_type', 'severity')
        }),
        ('Detection Details', {
            'fields': ('affected_columns', 'affected_rows', 'anomaly_score', 'details')
        }),
        ('Visualization', {
            'fields': ('visualization_data',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('acknowledged', 'detected_at')
        }),
    )


@admin.register(OutlierAnalysis)
class OutlierAnalysisAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'column', 'method', 'outlier_count', 'outlier_percentage', 'created_at')
    list_filter = ('method', 'created_at')
    search_fields = ('dataset__name', 'column')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Dataset & Column', {
            'fields': ('dataset', 'column', 'method')
        }),
        ('Results', {
            'fields': ('outlier_indices', 'outlier_values', 'outlier_count', 'outlier_percentage')
        }),
        ('Statistics', {
            'fields': ('threshold_values', 'statistics'),
            'classes': ('collapse',)
        }),
        ('Visualization', {
            'fields': ('visualization_data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(RelationshipAnalysis)
class RelationshipAnalysisAdmin(admin.ModelAdmin):
    list_display = ('feature_1', 'feature_2', 'correlation_coefficient', 'relationship_type', 'is_significant', 'created_at')
    list_filter = ('relationship_type', 'is_significant', 'created_at')
    search_fields = ('dataset__name', 'feature_1', 'feature_2')
    readonly_fields = ('created_at',)


@admin.register(ModelExplanation)
class ModelExplanationAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'model_type', 'target_variable', 'created_at', 'updated_at')
    list_filter = ('model_type', 'created_at')
    search_fields = ('dataset__name', 'model_type', 'target_variable')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InsightReport)
class InsightReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'dataset', 'owner', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'dataset__name', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    
    filter_horizontal = ('insights', 'anomalies', 'outlier_analyses', 'relationships')
