"""
DRF Serializers for insights app
"""

from rest_framework import serializers
from .models import (
    DataInsight, AnomalyDetection, OutlierAnalysis, 
    RelationshipAnalysis, ModelExplanation, InsightReport
)


class DataInsightSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = DataInsight
        fields = [
            'id', 'title', 'description', 'insight_type', 'dataset', 'dataset_name',
            'analysis_data', 'confidence_score', 'key_features',
            'shap_values', 'lime_explanation', 'human_explanation',
            'is_public', 'is_pinned', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'owner_name', 'created_at', 'updated_at']


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'dataset', 'dataset_name', 'anomaly_type', 'affected_columns',
            'affected_rows', 'severity', 'anomaly_score', 'details',
            'visualization_data', 'acknowledged', 'detected_at'
        ]
        read_only_fields = ['id', 'detected_at']


class OutlierAnalysisSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = OutlierAnalysis
        fields = [
            'id', 'dataset', 'dataset_name', 'column', 'method',
            'outlier_indices', 'outlier_values', 'outlier_count',
            'outlier_percentage', 'threshold_values', 'statistics',
            'visualization_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RelationshipAnalysisSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = RelationshipAnalysis
        fields = [
            'id', 'dataset', 'dataset_name', 'feature_1', 'feature_2',
            'correlation_coefficient', 'p_value', 'is_significant',
            'relationship_type', 'visualization_data', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ModelExplanationSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    
    class Meta:
        model = ModelExplanation
        fields = [
            'id', 'dataset', 'dataset_name', 'model_type', 'target_variable',
            'shap_summary', 'feature_importance', 'sample_explanations',
            'summary_plot_data', 'force_plot_data', 'dependence_plot_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InsightReportSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    insights_count = serializers.SerializerMethodField()
    anomalies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InsightReport
        fields = [
            'id', 'title', 'description', 'dataset', 'dataset_name',
            'owner', 'owner_name', 'summary', 'key_findings', 'recommendations',
            'insights_count', 'anomalies_count',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'owner_name', 'created_at', 'updated_at']
    
    def get_insights_count(self, obj):
        return obj.insights.count()
    
    def get_anomalies_count(self, obj):
        return obj.anomalies.count()
