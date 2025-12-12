"""
Views for insights and data analysis
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q, Avg
from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from datasets.models import Dataset
from .models import DataInsight, AnomalyDetection, OutlierAnalysis, RelationshipAnalysis, InsightReport
from .services import InsightGenerator
from core.views import create_notification

logger = logging.getLogger(__name__)


# ============================================================================
# INSIGHT VIEWS
# ============================================================================

class InsightListView(LoginRequiredMixin, ListView):
    """
    List user's datasets and select one to run insights
    Similar to visualization creation but for insights
    """
    model = Dataset
    template_name = 'insights/insight/list.html'
    context_object_name = 'datasets'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get user's datasets"""
        return Dataset.objects.filter(
            owner=self.request.user
        ).order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Stats for all insights
        context['total_insights'] = DataInsight.objects.filter(owner=user).count()
        context['total_anomalies'] = AnomalyDetection.objects.filter(
            dataset__owner=user
        ).count()
        context['total_outlier_analyses'] = OutlierAnalysis.objects.filter(
            dataset__owner=user
        ).count()
        context['total_relationships'] = RelationshipAnalysis.objects.filter(
            dataset__owner=user
        ).count()
        
        return context


class InsightDetailView(LoginRequiredMixin, DetailView):
    """
    Display detailed insight with SHAP/LIME explanations
    """
    model = DataInsight
    template_name = 'insights/insight/detail.html'
    context_object_name = 'insight'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Ensure user owns this insight"""
        return DataInsight.objects.filter(owner=self.request.user)


class DatasetInsightsView(LoginRequiredMixin, TemplateView):
    """
    Generate and display all insights for a specific dataset
    """
    template_name = 'insights/dataset_insights.html'
    login_url = 'accounts:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset_id = self.kwargs.get('dataset_id')
        
        # Verify ownership
        dataset = get_object_or_404(Dataset, id=dataset_id, owner=self.request.user)
        context['dataset'] = dataset
        
        # Get all insights for this dataset
        context['insights'] = DataInsight.objects.filter(dataset=dataset)
        context['anomalies'] = AnomalyDetection.objects.filter(dataset=dataset)
        context['outlier_analyses'] = OutlierAnalysis.objects.filter(dataset=dataset)
        context['relationships'] = RelationshipAnalysis.objects.filter(dataset=dataset)
        context['reports'] = InsightReport.objects.filter(dataset=dataset, owner=self.request.user)
        
        return context


class GenerateInsightsView(LoginRequiredMixin, TemplateView):
    """
    API view to generate insights for a dataset
    """
    def post(self, request, dataset_id):
        """Generate insights for dataset"""
        try:
            dataset = get_object_or_404(Dataset, id=dataset_id, owner=request.user)
            
            # Parse dataset file
            from datasets.services import FileParser
            df = FileParser.parse_file(dataset.file.path, dataset.file_type)
            
            # Generate insights
            generator = InsightGenerator(df, dataset_id)
            insights_data = generator.generate_all_insights()
            
            if 'error' in insights_data:
                return JsonResponse({'error': insights_data['error']}, status=400)
            
            # Save insights to database
            summary_insight = DataInsight.objects.create(
                owner=request.user,
                dataset=dataset,
                title=f"Dataset Summary - {dataset.name}",
                description="Automated summary statistics and overview",
                insight_type='summary',
                analysis_data=insights_data.get('summary_stats', {}),
                human_explanation=self._generate_summary_explanation(insights_data),
            )
            
            # Save anomalies
            for col, anomaly_data in insights_data.get('anomalies', {}).items():
                if anomaly_data['count'] > 0:
                    AnomalyDetection.objects.create(
                        insight=None,
                        dataset=dataset,
                        anomaly_type='statistical',
                        affected_columns=[col],
                        affected_rows=anomaly_data.get('indices', []),
                        severity=anomaly_data.get('severity', 'medium'),
                        anomaly_score=anomaly_data['percentage'] / 100,
                        details=anomaly_data,
                    )
            
            # Save relationships
            for rel_key, rel_data in insights_data.get('relationships', {}).items():
                RelationshipAnalysis.objects.create(
                    dataset=dataset,
                    feature_1=rel_data['feature_1'],
                    feature_2=rel_data['feature_2'],
                    correlation_coefficient=rel_data['correlation'],
                    is_significant=abs(rel_data['correlation']) > 0.3,
                    relationship_type=self._classify_relationship(rel_data['correlation']),
                    description=f"{rel_data['strength']} {rel_data['direction']} relationship",
                )
            
            # Create notification
            create_notification(
                user=request.user,
                title='Insights Generated',
                message=f'Insights generated for dataset: {dataset.name}',
                notification_type='success',
                related_app='insights',
                related_model='DataInsight',
                related_object_id=summary_insight.id
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Insights generated successfully',
                'insight_id': summary_insight.id,
                'insights_summary': {
                    'anomalies_detected': len(insights_data.get('anomalies', {})),
                    'outliers_detected': insights_data.get('outliers', {}).get('total_outliers', 0),
                    'relationships_found': len(insights_data.get('relationships', {})),
                }
            })
        
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    @staticmethod
    def _generate_summary_explanation(insights_data: dict) -> str:
        """Generate human-readable summary"""
        lines = []
        
        summary = insights_data.get('summary_stats', {})
        lines.append(f"Dataset contains {summary.get('rows', 0)} rows and {summary.get('columns', 0)} columns.")
        
        anomalies = insights_data.get('anomalies', {})
        if anomalies:
            lines.append(f"Found {len(anomalies)} columns with statistical anomalies.")
        
        relationships = insights_data.get('relationships', {})
        if relationships:
            lines.append(f"Identified {len(relationships)} significant correlations between features.")
        
        return " ".join(lines)
    
    @staticmethod
    def _classify_relationship(correlation: float) -> str:
        """Classify relationship type"""
        if correlation > 0.5:
            return 'linear'
        elif correlation < -0.5:
            return 'inverse'
        else:
            return 'non_linear'


class AnomalyListView(LoginRequiredMixin, ListView):
    """List detected anomalies"""
    model = AnomalyDetection
    template_name = 'insights/anomaly/list.html'
    context_object_name = 'anomalies'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get anomalies for user's datasets"""
        return AnomalyDetection.objects.filter(
            dataset__owner=self.request.user
        ).select_related('dataset').order_by('-anomaly_score')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anomalies = self.get_queryset()
        context['critical_count'] = anomalies.filter(severity='critical').count()
        context['high_count'] = anomalies.filter(severity='high').count()
        context['medium_count'] = anomalies.filter(severity='medium').count()
        return context


class AnomalyDetailView(LoginRequiredMixin, DetailView):
    """Display detailed anomaly information"""
    model = AnomalyDetection
    template_name = 'insights/anomaly/detail.html'
    context_object_name = 'anomaly'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Ensure user owns the dataset this anomaly is from"""
        return AnomalyDetection.objects.filter(dataset__owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anomaly = self.get_object()
        context['dataset'] = anomaly.dataset
        return context


class OutlierListView(LoginRequiredMixin, ListView):
    """List outlier analyses"""
    model = OutlierAnalysis
    template_name = 'insights/outlier/list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get outlier analyses for user's datasets"""
        return OutlierAnalysis.objects.filter(
            dataset__owner=self.request.user
        ).select_related('dataset').order_by('-outlier_percentage')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analyses = self.get_queryset()
        context['total_outliers'] = sum(a.outlier_count for a in analyses)
        context['avg_percentage'] = analyses.aggregate(
            avg=models.Avg('outlier_percentage')
        )['avg'] or 0
        return context


class OutlierDetailView(LoginRequiredMixin, DetailView):
    """Display detailed outlier analysis"""
    model = OutlierAnalysis
    template_name = 'insights/outlier/detail.html'
    context_object_name = 'analysis'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Ensure user owns the dataset this analysis is from"""
        return OutlierAnalysis.objects.filter(dataset__owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.get_object()
        context['dataset'] = analysis.dataset
        return context


class RelationshipListView(LoginRequiredMixin, ListView):
    """List relationship analyses"""
    model = RelationshipAnalysis
    template_name = 'insights/relationship/list.html'
    context_object_name = 'relationships'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get relationships for user's datasets"""
        return RelationshipAnalysis.objects.filter(
            dataset__owner=self.request.user
        ).select_related('dataset').order_by('-correlation_coefficient')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        relationships = self.get_queryset()
        context['significant_count'] = relationships.filter(is_significant=True).count()
        context['linear_count'] = relationships.filter(relationship_type='linear').count()
        context['inverse_count'] = relationships.filter(relationship_type='inverse').count()
        return context


class RelationshipDetailView(LoginRequiredMixin, DetailView):
    """Display detailed relationship analysis"""
    model = RelationshipAnalysis
    template_name = 'insights/relationship/detail.html'
    context_object_name = 'relationship'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Ensure user owns the dataset this relationship is from"""
        return RelationshipAnalysis.objects.filter(dataset__owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        relationship = self.get_object()
        context['dataset'] = relationship.dataset
        return context


class RunInsightsAPIView(LoginRequiredMixin, View):
    """
    API endpoint to run insights on a dataset
    Similar to how visualizations work - runs all analysis functions
    """
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Run insights for a dataset"""
        try:
            import pandas as pd
            import json
            
            dataset_id = request.POST.get('dataset_id') or request.data.get('dataset_id')
            if not dataset_id:
                return JsonResponse({'status': 'error', 'message': 'dataset_id required'}, status=400)
            
            # Verify ownership
            dataset = get_object_or_404(Dataset, id=dataset_id, owner=request.user)
            
            # Load dataset
            if not dataset.file:
                return JsonResponse({'status': 'error', 'message': 'Dataset file not found'}, status=400)
            
            # Read file
            file_path = dataset.file.path
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                return JsonResponse({'status': 'error', 'message': 'Unsupported file format'}, status=400)
            
            # Generate insights
            generator = InsightGenerator(df, dataset.id)
            results = generator.generate_all_insights()
            
            # Clean up old analyses to avoid UNIQUE constraint violations
            AnomalyDetection.objects.filter(dataset=dataset).delete()
            OutlierAnalysis.objects.filter(dataset=dataset).delete()
            RelationshipAnalysis.objects.filter(dataset=dataset).delete()
            
            # Create main insight
            insight = DataInsight.objects.create(
                dataset=dataset,
                owner=request.user,
                title=f'Analysis - {dataset.name}',
                description=f'Comprehensive analysis of {dataset.name}',
                insight_type='summary',
                analysis_data=results,
                confidence_score=92.5
            )
            
            # Save anomalies
            anomalies = results.get('anomalies', {})
            for col, anomaly_data in anomalies.items():
                if anomaly_data and anomaly_data.get('count', 0) > 0:
                    AnomalyDetection.objects.create(
                        dataset=dataset,
                        affected_columns=[col],
                        anomaly_type='statistical',
                        affected_rows=anomaly_data.get('indices', []),
                        severity='high' if anomaly_data.get('count', 0) > 5 else 'medium',
                        anomaly_score=float(anomaly_data.get('count', 0)) / len(df) if len(df) > 0 else 0,
                        details=anomaly_data
                    )
            
            # Save outliers
            outliers = results.get('outliers', {})
            if 'outlier_indices' in outliers and isinstance(outliers['outlier_indices'], list):
                if len(outliers['outlier_indices']) > 0:
                    OutlierAnalysis.objects.create(
                        dataset=dataset,
                        column='combined',
                        method='isolation_forest',
                        outlier_indices=outliers['outlier_indices'],
                        outlier_count=len(outliers['outlier_indices']),
                        outlier_percentage=outliers['summary'].get('outlier_percentage', 0),
                        statistics=outliers.get('summary', {})
                    )
            
            # Save relationships
            relationships = results.get('relationships', {})
            # Handle both dict and list formats
            rel_items = relationships.values() if isinstance(relationships, dict) else relationships
            for rel in rel_items:
                RelationshipAnalysis.objects.create(
                    dataset=dataset,
                    feature_1=rel.get('feature_1', ''),
                    feature_2=rel.get('feature_2', ''),
                    correlation_coefficient=rel.get('correlation', 0),
                    p_value=rel.get('p_value', 0),
                    relationship_type=rel.get('relationship_type', 'linear'),
                    description=rel.get('description', f"{rel.get('strength', '')} {rel.get('direction', '')} relationship".strip()),
                )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Insights generated successfully',
                'insight_id': insight.id,
                'results': {
                    'anomalies': len(anomalies),
                    'outliers': len(outliers),
                    'relationships': len(relationships),
                }
            })
        
        except Exception as e:
            logger.error(f"Error running insights: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================================================
# REST API VIEWSETS
# ============================================================================

class InsightViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing insights
    """
    serializer_class = None  # Implement serializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's insights"""
        return DataInsight.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set owner to current user"""
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_dataset(self, request):
        """Get insights for a specific dataset"""
        dataset_id = request.query_params.get('dataset_id')
        if not dataset_id:
            return Response({'error': 'dataset_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        insights = self.get_queryset().filter(dataset_id=dataset_id)
        # Implement serializer response
        return Response({'insights': []})


class AnomalyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing anomalies
    """
    serializer_class = None  # Implement serializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's datasets' anomalies"""
        return AnomalyDetection.objects.filter(dataset__owner=self.request.user)


class OutlierViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing outlier analyses
    """
    serializer_class = None  # Implement serializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's datasets' outliers"""
        return OutlierAnalysis.objects.filter(dataset__owner=self.request.user)
