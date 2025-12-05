"""
Analytics views for LuminaBI.
Handles displaying insights, reports, trends, and anomalies.
"""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Insight, Report, Trend, Anomaly, Alert, Metric, AnalyticsDashboard
from datasets.models import Dataset
from core.mixins import OwnerRequiredMixin

logger = logging.getLogger(__name__)


# ============================================================================
# INSIGHT VIEWS
# ============================================================================

class InsightListView(LoginRequiredMixin, ListView):
    """
    List all insights for user's datasets.
    Shows recent insights with filters.
    """
    model = Insight
    template_name = 'analytics/insight/list.html'
    context_object_name = 'insights'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get insights for user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        queryset = Insight.objects.filter(dataset__in=user_datasets).order_by('-created_at')
        
        # Filter by insight type
        insight_type = self.request.GET.get('type')
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        
        # Filter by dataset
        dataset_id = self.request.GET.get('dataset')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        
        # Filter by confidence level
        confidence = self.request.GET.get('confidence')
        if confidence:
            queryset = queryset.filter(confidence_level=confidence)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        context['datasets'] = user_datasets
        context['insight_types'] = Insight.INSIGHT_TYPES
        context['confidence_levels'] = Insight.CONFIDENCE_LEVELS
        context['current_type'] = self.request.GET.get('type', '')
        context['current_confidence'] = self.request.GET.get('confidence', '')
        
        # Statistics
        context['total_insights'] = Insight.objects.filter(dataset__in=user_datasets).count()
        context['validated_insights'] = Insight.objects.filter(
            dataset__in=user_datasets,
            is_validated=True
        ).count()
        context['recent_insights'] = Insight.objects.filter(
            dataset__in=user_datasets,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return context


class InsightDetailView(LoginRequiredMixin, DetailView):
    """Display a single insight with full details."""
    model = Insight
    template_name = 'analytics/insight/detail.html'
    context_object_name = 'insight'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show insights from user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Insight.objects.filter(dataset__in=user_datasets)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        insight = self.get_object()
        context['related_insights'] = Insight.objects.filter(
            dataset=insight.dataset,
            insight_type=insight.insight_type
        ).exclude(id=insight.id)[:5]
        return context


class InsightValidateView(LoginRequiredMixin, DetailView):
    """Validate or invalidate an insight."""
    model = Insight
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle validation action."""
        insight = self.get_object()
        action = request.POST.get('action', 'validate')
        notes = request.POST.get('notes', '')
        
        if action == 'validate':
            insight.is_validated = True
            insight.validated_by = request.user
            insight.validated_at = timezone.now()
        elif action == 'invalidate':
            insight.is_validated = False
            insight.validated_by = None
            insight.validated_at = None
        
        if notes:
            insight.validation_notes = notes
        
        insight.save()
        return redirect('analytics:insight_detail', pk=insight.pk)


# ============================================================================
# REPORT VIEWS
# ============================================================================

class ReportListView(LoginRequiredMixin, ListView):
    """
    List all reports for user's datasets.
    Shows reports with filtering by status and type.
    """
    model = Report
    template_name = 'analytics/report/list.html'
    context_object_name = 'reports'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get reports for user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        queryset = Report.objects.filter(dataset__in=user_datasets).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by report type
        report_type = self.request.GET.get('type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by dataset
        dataset_id = self.request.GET.get('dataset')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        context['datasets'] = user_datasets
        context['report_types'] = Report.REPORT_TYPES
        context['statuses'] = Report.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        
        # Statistics
        context['total_reports'] = Report.objects.filter(dataset__in=user_datasets).count()
        context['published_reports'] = Report.objects.filter(
            dataset__in=user_datasets,
            status='published'
        ).count()
        context['draft_reports'] = Report.objects.filter(
            dataset__in=user_datasets,
            status='draft'
        ).count()
        
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    """Display a single report with full details."""
    model = Report
    template_name = 'analytics/report/detail.html'
    context_object_name = 'report'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show reports from user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Report.objects.filter(dataset__in=user_datasets)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        context['related_reports'] = Report.objects.filter(
            dataset=report.dataset,
            report_type=report.report_type
        ).exclude(id=report.id)[:5]
        return context


class ReportPublishView(LoginRequiredMixin, DetailView):
    """Publish a report."""
    model = Report
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle publish action."""
        report = self.get_object()
        report.publish()
        return redirect('analytics:report_detail', pk=report.pk)


# ============================================================================
# ANOMALY VIEWS
# ============================================================================

class AnomalyListView(LoginRequiredMixin, ListView):
    """
    List all anomalies for user's datasets.
    Shows anomalies with filtering by severity and status.
    """
    model = Anomaly
    template_name = 'analytics/anomaly/list.html'
    context_object_name = 'anomalies'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get anomalies for user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        queryset = Anomaly.objects.filter(dataset__in=user_datasets).order_by('-detected_at')
        
        # Filter by severity
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by dataset
        dataset_id = self.request.GET.get('dataset')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        context['datasets'] = user_datasets
        context['severities'] = Anomaly.SEVERITY_LEVELS
        context['statuses'] = Anomaly.STATUS_CHOICES
        context['current_severity'] = self.request.GET.get('severity', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # Statistics
        context['total_anomalies'] = Anomaly.objects.filter(dataset__in=user_datasets).count()
        context['critical_anomalies'] = Anomaly.objects.filter(
            dataset__in=user_datasets,
            severity='critical'
        ).count()
        context['unresolved_anomalies'] = Anomaly.objects.filter(
            dataset__in=user_datasets,
            status__in=['new', 'acknowledged', 'investigating']
        ).count()
        
        return context


class AnomalyDetailView(LoginRequiredMixin, DetailView):
    """Display a single anomaly with full details."""
    model = Anomaly
    template_name = 'analytics/anomaly/detail.html'
    context_object_name = 'anomaly'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show anomalies from user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Anomaly.objects.filter(dataset__in=user_datasets)


class AnomalyAcknowledgeView(LoginRequiredMixin, DetailView):
    """Acknowledge an anomaly."""
    model = Anomaly
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle acknowledge action."""
        anomaly = self.get_object()
        anomaly.acknowledge(user=request.user)
        return JsonResponse({'success': True, 'message': 'Anomaly acknowledged'})


class AnomalyResolveView(LoginRequiredMixin, DetailView):
    """Resolve an anomaly."""
    model = Anomaly
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle resolve action."""
        anomaly = self.get_object()
        notes = request.POST.get('notes', '')
        anomaly.resolve(resolution_notes=notes)
        return JsonResponse({'success': True, 'message': 'Anomaly resolved'})


# ============================================================================
# ALERT VIEWS
# ============================================================================

class AlertListView(LoginRequiredMixin, ListView):
    """
    List all alerts for user's datasets.
    Shows active and recent alerts.
    """
    model = Alert
    template_name = 'analytics/alert/list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get alerts for user."""
        queryset = Alert.objects.filter(recipients=self.request.user).order_by('-triggered_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by level
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(alert_level=level)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_levels'] = Alert.ALERT_LEVELS
        context['statuses'] = Alert.STATUS_CHOICES
        context['current_level'] = self.request.GET.get('level', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # Statistics
        context['total_alerts'] = Alert.objects.filter(recipients=self.request.user).count()
        context['active_alerts'] = Alert.objects.filter(
            recipients=self.request.user,
            status='active'
        ).count()
        context['critical_alerts'] = Alert.objects.filter(
            recipients=self.request.user,
            alert_level='critical'
        ).count()
        
        return context


class AlertAcknowledgeView(LoginRequiredMixin, DetailView):
    """Acknowledge an alert."""
    model = Alert
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle acknowledge action."""
        alert = self.get_object()
        alert.acknowledge()
        return JsonResponse({'success': True, 'message': 'Alert acknowledged'})


class AlertResolveView(LoginRequiredMixin, DetailView):
    """Resolve an alert."""
    model = Alert
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Handle resolve action."""
        alert = self.get_object()
        alert.resolve()
        return JsonResponse({'success': True, 'message': 'Alert resolved'})


# ============================================================================
# DASHBOARD VIEWS
# ============================================================================

class DashboardListView(LoginRequiredMixin, ListView):
    """
    List all dashboards for user.
    Shows owned and shared dashboards.
    """
    model = AnalyticsDashboard
    template_name = 'analytics/dashboard/list.html'
    context_object_name = 'dashboards'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get dashboards owned by or shared with user."""
        return AnalyticsDashboard.objects.filter(
            Q(owner=self.request.user) | Q(shared_with=self.request.user)
        ).distinct().order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owned_dashboards'] = AnalyticsDashboard.objects.filter(owner=self.request.user).count()
        context['shared_dashboards'] = AnalyticsDashboard.objects.filter(
            shared_with=self.request.user
        ).count()
        return context


class DashboardDetailView(LoginRequiredMixin, DetailView):
    """Display a dashboard with all widgets and metrics."""
    model = AnalyticsDashboard
    template_name = 'analytics/dashboard/detail.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show dashboards user owns or is shared with."""
        return AnalyticsDashboard.objects.filter(
            Q(owner=self.request.user) | Q(shared_with=self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.get_object()
        
        # Get all related data
        context['insights'] = dashboard.insights.all()[:10]
        context['metrics'] = dashboard.metrics.all()[:10]
        context['datasets'] = dashboard.datasets.all()[:10]
        
        # Statistics
        context['insight_count'] = dashboard.insights.count()
        context['metric_count'] = dashboard.metrics.count()
        context['dataset_count'] = dashboard.datasets.count()
        
        return context


class DashboardCreateView(LoginRequiredMixin, CreateView):
    """Create a new dashboard."""
    model = AnalyticsDashboard
    template_name = 'analytics/dashboard/form.html'
    fields = ['name', 'description', 'is_public']
    success_url = reverse_lazy('analytics:dashboard_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class DashboardUpdateView(LoginRequiredMixin, UpdateView):
    """Update a dashboard."""
    model = AnalyticsDashboard
    template_name = 'analytics/dashboard/form.html'
    fields = ['name', 'description', 'is_public']
    success_url = reverse_lazy('analytics:dashboard_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to update."""
        return AnalyticsDashboard.objects.filter(owner=self.request.user)


class DashboardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a dashboard."""
    model = AnalyticsDashboard
    template_name = 'analytics/dashboard/confirm_delete.html'
    success_url = reverse_lazy('analytics:dashboard_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to delete."""
        return AnalyticsDashboard.objects.filter(owner=self.request.user)


# ============================================================================
# METRIC VIEWS
# ============================================================================

class MetricListView(LoginRequiredMixin, ListView):
    """
    List all metrics for user's datasets.
    Shows key performance indicators.
    """
    model = Metric
    template_name = 'analytics/metric/list.html'
    context_object_name = 'metrics'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get metrics for user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        queryset = Metric.objects.filter(dataset__in=user_datasets).order_by('-updated_at')
        
        # Filter by dataset
        dataset_id = self.request.GET.get('dataset')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        context['datasets'] = user_datasets
        context['current_status'] = self.request.GET.get('status', '')
        
        # Statistics
        context['total_metrics'] = Metric.objects.filter(dataset__in=user_datasets).count()
        context['warning_metrics'] = Metric.objects.filter(
            dataset__in=user_datasets
        ).filter(Q(status='warning') | Q(status='critical')).count()
        
        return context


class MetricDetailView(LoginRequiredMixin, DetailView):
    """Display a single metric with history."""
    model = Metric
    template_name = 'analytics/metric/detail.html'
    context_object_name = 'metric'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show metrics from user's datasets."""
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        return Metric.objects.filter(dataset__in=user_datasets)


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main analytics dashboard.
    Aggregates all analytics for user's datasets.
    """
    template_name = 'analytics/dashboard.html'
    login_url = 'accounts:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_datasets = Dataset.objects.filter(owner=self.request.user)
        
        # Overview statistics
        context['total_datasets'] = user_datasets.count()
        context['total_insights'] = Insight.objects.filter(dataset__in=user_datasets).count()
        context['total_anomalies'] = Anomaly.objects.filter(dataset__in=user_datasets).count()
        context['total_alerts'] = Alert.objects.filter(recipients=self.request.user).count()
        
        # Recent activity
        context['recent_insights'] = Insight.objects.filter(
            dataset__in=user_datasets
        ).order_by('-created_at')[:5]
        
        context['critical_anomalies'] = Anomaly.objects.filter(
            dataset__in=user_datasets,
            severity='critical',
            status__in=['new', 'acknowledged', 'investigating']
        ).order_by('-detected_at')[:5]
        
        context['active_alerts'] = Alert.objects.filter(
            recipients=self.request.user,
            status='active'
        ).order_by('-triggered_at')[:5]
        
        context['top_metrics'] = Metric.objects.filter(
            dataset__in=user_datasets
        ).order_by('-updated_at')[:10]
        
        return context
