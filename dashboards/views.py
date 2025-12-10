"""
Enhanced Dashboard views for LuminaBI.
Provides automatic insights, ML interpretability, and intelligent analytics.
"""

import json
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Dashboard, DashboardWidget, DashboardInsight, 
    InterpretabilityAnalysis, DashboardShare
)
from .serializers import DashboardSerializer, DashboardInsightSerializer, DashboardSummarySerializer, DashboardWidgetSerializer, InterpretabilityAnalysisSerializer
from analytics.models import Insight, Anomaly, Metric, Alert
from visualizations.models import Visualization
from datasets.models import Dataset
from core.views import create_notification

logger = logging.getLogger(__name__)


# ============================================================================
# DASHBOARD CRUD VIEWS
# ============================================================================

class DashboardListView(LoginRequiredMixin, ListView):
    """List all dashboards for the current user."""
    model = Dashboard
    template_name = 'dashboards/dashboard/list.html'
    context_object_name = 'dashboards'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get dashboards owned by or shared with user."""
        user = self.request.user
        owned = Q(owner=user)
        shared = Q(shares__shared_with=user, shares__expires_at__gt=timezone.now()) | \
                Q(shares__shared_with=user, shares__expires_at__isnull=True)
        
        return Dashboard.objects.filter(owned | shared).distinct().order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistics
        context['total_dashboards'] = Dashboard.objects.filter(owner=user).count()
        context['published_dashboards'] = Dashboard.objects.filter(
            owner=user, 
            is_published=True
        ).count()
        context['shared_with_me'] = DashboardShare.objects.filter(
            shared_with=user
        ).count()
        context['template_dashboards'] = Dashboard.objects.filter(
            is_template=True
        ).count()

        # Live hub data: surface recent activity so the list page is useful
        context['recent_datasets'] = Dataset.objects.filter(
            owner=user
        ).order_by('-uploaded_at')[:6]

        context['recent_insights'] = Insight.objects.filter(
            dataset__owner=user
        ).order_by('-created_at')[:6]

        context['recent_anomalies'] = Anomaly.objects.filter(
            dataset__owner=user
        ).order_by('-detected_at')[:6]

        context['recent_metrics'] = Metric.objects.filter(
            dataset__owner=user
        ).order_by('-updated_at')[:6]
        
        return context


class DashboardDetailView(LoginRequiredMixin, DetailView):
    """
    Display comprehensive dashboard with all widgets, insights, and analytics.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/detail.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_object(self):
        """Get dashboard and check access permissions."""
        obj = super().get_object()
        user = self.request.user
        
        # Check if user owns or has access
        if obj.owner != user:
            share = DashboardShare.objects.filter(
                dashboard=obj,
                shared_with=user
            ).first()
            
            if not share or share.is_expired:
                if not obj.is_published:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("You don't have access to this dashboard")
        
        # Increment view count
        obj.increment_view_count()
        
        # Refresh insights if needed
        if obj.needs_insight_refresh():
            self._refresh_dashboard_insights(obj)
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.get_object()
        user = self.request.user
        
        # Access control
        context['is_owner'] = dashboard.owner == user
        context['can_edit'] = context['is_owner'] or self._user_can_edit(dashboard, user)
        
        # Widgets
        context['widgets'] = dashboard.widgets.filter(is_visible=True).order_by(
            'position_y', 'position_x'
        )
        
        # Visualizations
        visualizations = dashboard.visualizations.all()
        context['visualizations'] = visualizations
        context['visualization_data'] = self._prepare_visualization_data(visualizations)
        
        # Dashboard insights
        context['insights'] = dashboard.dashboard_insights.filter(
            Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True)
        ).order_by('-priority', '-generated_at')[:20]
        
        # Actionable insights
        context['actionable_insights'] = dashboard.dashboard_insights.filter(
            is_actionable=True,
            action_taken=False
        ).order_by('-priority')
        
        # Analytics from related datasets
        datasets = dashboard.datasets.all()
        context['datasets'] = datasets
        context['dataset_insights'] = Insight.objects.filter(
            dataset__in=datasets
        ).order_by('-created_at')[:10]
        
        context['anomalies'] = Anomaly.objects.filter(
            dataset__in=datasets,
            status__in=['new', 'acknowledged', 'investigating']
        ).order_by('-severity', '-detected_at')[:10]
        
        context['metrics'] = Metric.objects.filter(
            dataset__in=datasets
        ).order_by('-updated_at')[:10]
        
        # Interpretability analyses
        if dashboard.interpretability_enabled:
            context['interpretability_analyses'] = dashboard.interpretability_analyses.order_by(
                '-created_at'
            )[:5]

        # Dataset summaries for overview cards
        dataset_summaries = []
        for ds in datasets:
            dataset_summaries.append({
                'id': ds.id,
                'name': ds.name,
                'rows': ds.row_count,
                'cols': ds.col_count,
                'quality': ds.data_quality_score,
                'is_cleaned': ds.is_cleaned,
                'summary': (ds.summary[:180] + '...') if ds.summary and len(ds.summary) > 180 else ds.summary,
                'uploaded_at': ds.uploaded_at,
            })
        context['dataset_summaries'] = dataset_summaries

        # Insights grouped by dataset for quick navigation
        insights_grouped = {}
        for insight in context['dataset_insights']:
            key = insight.dataset_id
            if key not in insights_grouped:
                insights_grouped[key] = []
            insights_grouped[key].append(insight)
        context['insights_grouped'] = insights_grouped
        
        # Summary statistics
        context['summary_stats'] = {
            'total_insights': dashboard.dashboard_insights.count(),
            'critical_insights': dashboard.dashboard_insights.filter(priority='critical').count(),
            'actionable_count': dashboard.dashboard_insights.filter(
                is_actionable=True, 
                action_taken=False
            ).count(),
            'widget_count': dashboard.widgets.count(),
            'visualization_count': visualizations.count(),
            'dataset_count': datasets.count(),
        }
        
        return context
    
    def _user_can_edit(self, dashboard, user):
        """Check if user has edit permissions."""
        share = DashboardShare.objects.filter(
            dashboard=dashboard,
            shared_with=user
        ).first()
        return share and share.can_edit() and not share.is_expired
    
    def _prepare_visualization_data(self, visualizations):
        """Prepare visualization data for Chart.js rendering."""
        vis_data = {}
        for vis in visualizations:
            if vis.config and isinstance(vis.config, dict):
                vis_data[vis.id] = {
                    'title': vis.title,
                    'type': vis.chart_type,
                    'data': vis.config
                }
            else:
                # Default fallback
                vis_data[vis.id] = {
                    'title': vis.title,
                    'type': vis.chart_type,
                    'data': {
                        'labels': ['Data 1', 'Data 2', 'Data 3'],
                        'datasets': [{
                            'label': vis.title,
                            'data': [10, 20, 30],
                        }]
                    }
                }
        return json.dumps(vis_data)
    
    def _refresh_dashboard_insights(self, dashboard):
        """
        Refresh dashboard insights by analyzing current data.
        This would integrate with your analytics engine.
        """
        try:
            # Mark as refreshed
            dashboard.last_insight_refresh = timezone.now()
            dashboard.save(update_fields=['last_insight_refresh'])
            
            # Trigger insight generation (implement in background task)
            from .tasks import generate_dashboard_insights
            generate_dashboard_insights.delay(dashboard.id)
            
        except Exception as e:
            logger.error(f"Error refreshing insights for dashboard {dashboard.id}: {e}")


class DashboardCreateView(LoginRequiredMixin, CreateView):
    """Create a new dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = [
        'name', 'description', 'auto_insights_enabled', 
        'interpretability_enabled', 'interpretability_method'
    ]
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        """Set owner and initialize default settings."""
        form.instance.owner = self.request.user
        form.instance.settings = {
            'theme': 'light',
            'refresh_interval': 300,  # 5 minutes
            'show_timestamps': True,
        }
        response = super().form_valid(form)
        
        # Create notification
        create_notification(
            user=self.request.user,
            title='Dashboard Created',
            message=f'Dashboard "{form.instance.name}" has been created successfully.',
            notification_type='success',
            related_app='dashboards',
            related_model='Dashboard',
            related_object_id=form.instance.id
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Dashboard'
        context['button_text'] = 'Create Dashboard'
        return context


class DashboardUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = [
        'name', 'description', 'auto_insights_enabled',
        'insight_refresh_interval', 'interpretability_enabled',
        'interpretability_method'
    ]
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to update."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('dashboards:dashboard_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Dashboard'
        context['button_text'] = 'Save Changes'
        return context


class DashboardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a dashboard."""
    model = Dashboard
    template_name = 'dashboards/dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to delete."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Delete and notify."""
        obj = self.get_object()
        dashboard_name = obj.name
        response = super().delete(request, *args, **kwargs)
        
        create_notification(
            user=request.user,
            title='Dashboard Deleted',
            message=f'Dashboard "{dashboard_name}" has been deleted.',
            notification_type='info',
            related_app='dashboards',
            related_model='Dashboard'
        )
        
        return response


class DashboardPublishView(LoginRequiredMixin, DetailView):
    """
    Publish or unpublish a dashboard.
    """
    model = Dashboard
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Toggle publish status."""
        dashboard = self.get_object()
        action = request.POST.get('action', 'publish')
        
        if action == 'publish':
            dashboard.is_published = True
        elif action == 'unpublish':
            dashboard.is_published = False
        
        dashboard.save()
        return redirect('dashboards:dashboard_detail', pk=dashboard.pk)
    

class DashboardLayoutView(LoginRequiredMixin, DetailView):
    """
    View and edit dashboard layout.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/layout.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Save layout configuration."""
        dashboard = self.get_object()
        try:
            layout_data = json.loads(request.body)
            dashboard.layout = layout_data
            dashboard.save()
            return JsonResponse({'success': True, 'message': 'Layout saved'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)




class DashboardVisualizationView(LoginRequiredMixin, DetailView):
    """
    Manage visualizations on a dashboard.
    """
    model = Dashboard
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Dashboard.objects.filter(owner=self.request.user)
    
    def post(self, request, *args, **kwargs):
        """Add or remove visualizations."""
        dashboard = self.get_object()
        action = request.POST.get('action', 'add')
        visualization_id = request.POST.get('visualization_id')
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            
            if action == 'add':
                dashboard.visualizations.add(visualization)
                message = 'Visualization added to dashboard'
            elif action == 'remove':
                dashboard.visualizations.remove(visualization)
                message = 'Visualization removed from dashboard'
            
            return JsonResponse({'success': True, 'message': message})
        except Visualization.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Visualization not found'}, status=404)


# ============================================================================
# DASHBOARD INSIGHTS VIEWS
# ============================================================================

class DashboardInsightsView(LoginRequiredMixin, ListView):
    """View all insights for a specific dashboard."""
    model = DashboardInsight
    template_name = 'dashboards/insights/list.html'
    context_object_name = 'insights'
    paginate_by = 30
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get insights for the specified dashboard."""
        dashboard_id = self.kwargs.get('pk')
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id, owner=self.request.user)
        
        queryset = DashboardInsight.objects.filter(dashboard=dashboard)
        
        # Filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', '-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = self.kwargs.get('pk')
        context['dashboard'] = get_object_or_404(Dashboard, pk=dashboard_id)
        context['categories'] = DashboardInsight.INSIGHT_CATEGORIES
        context['priorities'] = DashboardInsight.PRIORITY_LEVELS
        return context


class InsightAcknowledgeView(LoginRequiredMixin, DetailView):
    """Acknowledge a dashboard insight."""
    model = DashboardInsight
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Mark insight as acknowledged."""
        insight = self.get_object()
        
        # Verify access
        if insight.dashboard.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        insight.acknowledge()
        
        return JsonResponse({
            'success': True,
            'message': 'Insight acknowledged',
            'action_taken': insight.action_taken
        })


# ============================================================================
# INTERPRETABILITY VIEWS
# ============================================================================

class InterpretabilityAnalysisView(LoginRequiredMixin, ListView):
    """View ML interpretability analyses for a dashboard."""
    model = InterpretabilityAnalysis
    template_name = 'dashboards/interpretability/list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get analyses for the specified dashboard."""
        dashboard_id = self.kwargs.get('pk')
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id, owner=self.request.user)
        return InterpretabilityAnalysis.objects.filter(dashboard=dashboard).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = self.kwargs.get('pk')
        context['dashboard'] = get_object_or_404(Dashboard, pk=dashboard_id)
        context['analysis_types'] = InterpretabilityAnalysis.ANALYSIS_TYPES
        return context


class InterpretabilityDetailView(LoginRequiredMixin, DetailView):
    """View detailed interpretability analysis results."""
    model = InterpretabilityAnalysis
    template_name = 'dashboards/interpretability/detail.html'
    context_object_name = 'analysis'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show analyses from user's dashboards."""
        return InterpretabilityAnalysis.objects.filter(dashboard__owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.get_object()
        
        # Prepare visualization data
        context['viz_data'] = json.dumps(analysis.visualization_data)
        context['top_features'] = analysis.top_features(n=15)
        
        return context


# ============================================================================
# DASHBOARD ACTIONS
# ============================================================================

class DashboardRefreshInsightsView(LoginRequiredMixin, DetailView):
    """Manually trigger insight refresh for a dashboard."""
    model = Dashboard
    login_url = 'accounts:login'
    
    def post(self, request, *args, **kwargs):
        """Trigger insight refresh."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Trigger refresh
        dashboard.last_insight_refresh = timezone.now()
        dashboard.save(update_fields=['last_insight_refresh'])
        
        # Queue background task
        try:
            from .tasks import generate_dashboard_insights
            generate_dashboard_insights.delay(dashboard.id)
            message = 'Insight refresh started'
        except:
            message = 'Insight refresh scheduled'
        
        return JsonResponse({'success': True, 'message': message})


class DashboardViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Dashboard model.
    Provides CRUD operations and intelligent dashboard management.
    """
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        """Use summary serializer for list, full for detail."""
        if self.action == 'list':
            return DashboardSummarySerializer
        return DashboardSerializer
    
    def get_queryset(self):
        """Filter dashboards - user's owned and shared ones."""
        user = self.request.user
        owned = Q(owner=user)
        shared = Q(shares__shared_with=user)
        
        return Dashboard.objects.filter(owned | shared).distinct()
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    def perform_update(self, serializer):
        """Verify ownership or edit permission on update."""
        instance = serializer.instance
        user = self.request.user
        
        if instance.owner != user:
            # Check if user has edit permission
            share = DashboardShare.objects.filter(
                dashboard=instance,
                shared_with=user
            ).first()
            
            if not share or not share.can_edit() or share.is_expired:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a dashboard (make it publicly viewable)."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can publish a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard.is_published = True
        dashboard.save()
        
        return Response({
            'status': 'dashboard published',
            'is_published': True
        })
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a dashboard."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can unpublish a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dashboard.is_published = False
        dashboard.save()
        
        return Response({
            'status': 'dashboard unpublished',
            'is_published': False
        })
    
    @action(detail=True, methods=['post'])
    def add_visualization(self, request, pk=None):
        """Add a visualization to the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        if not visualization_id:
            return Response(
                {'error': 'visualization_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            
            # Check if user can add this visualization
            if visualization.owner != request.user and not visualization.is_public:
                return Response(
                    {'error': 'You do not have access to this visualization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            dashboard.visualizations.add(visualization)
            
            return Response({
                'status': 'visualization added',
                'visualization_id': visualization_id
            })
        except Visualization.DoesNotExist:
            return Response(
                {'error': 'Visualization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_visualization(self, request, pk=None):
        """Remove a visualization from the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        if not visualization_id:
            return Response(
                {'error': 'visualization_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            dashboard.visualizations.remove(visualization)
            
            return Response({
                'status': 'visualization removed',
                'visualization_id': visualization_id
            })
        except Visualization.DoesNotExist:
            return Response(
                {'error': 'Visualization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def add_dataset(self, request, pk=None):
        """Add a dataset to monitor for insights."""
        dashboard = self.get_object()
        dataset_id = request.data.get('dataset_id')
        
        if not dataset_id:
            return Response(
                {'error': 'dataset_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from datasets.models import Dataset
        
        try:
            dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
            dashboard.datasets.add(dataset)
            
            return Response({
                'status': 'dataset added',
                'dataset_id': dataset_id
            })
        except Dataset.DoesNotExist:
            return Response(
                {'error': 'Dataset not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_layout(self, request, pk=None):
        """Update dashboard layout configuration."""
        dashboard = self.get_object()
        layout = request.data.get('layout', {})
        
        if not isinstance(layout, dict):
            return Response(
                {'error': 'layout must be a JSON object'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dashboard.layout = layout
        dashboard.save()
        
        return Response({
            'status': 'layout updated',
            'layout': dashboard.layout
        })
    
    @action(detail=True, methods=['post'])
    def refresh_insights(self, request, pk=None):
        """Manually trigger insight refresh."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can refresh insights'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update refresh timestamp
        dashboard.last_insight_refresh = timezone.now()
        dashboard.save(update_fields=['last_insight_refresh'])
        
        # Queue background task for insight generation
        try:
            from .tasks import generate_dashboard_insights
            generate_dashboard_insights.delay(dashboard.id)
            message = 'Insight generation queued'
        except ImportError:
            # Fallback if Celery not configured
            message = 'Insight refresh scheduled'
        
        return Response({
            'status': 'success',
            'message': message,
            'last_refresh': dashboard.last_insight_refresh
        })
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get all insights for this dashboard."""
        dashboard = self.get_object()
        insights = dashboard.dashboard_insights.filter(
            Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True)
        ).order_by('-priority', '-generated_at')
        
        # Apply filters
        category = request.query_params.get('category')
        if category:
            insights = insights.filter(category=category)
        
        priority = request.query_params.get('priority')
        if priority:
            insights = insights.filter(priority=priority)
        
        serializer = DashboardInsightSerializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def interpretability(self, request, pk=None):
        """Get interpretability analyses for this dashboard."""
        dashboard = self.get_object()
        
        if not dashboard.interpretability_enabled:
            return Response({
                'error': 'Interpretability not enabled for this dashboard'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analyses = dashboard.interpretability_analyses.order_by('-created_at')
        serializer = InterpretabilityAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about user's dashboards."""
        user = request.user
        user_dashboards = Dashboard.objects.filter(owner=user)
        
        return Response({
            'total_dashboards': user_dashboards.count(),
            'published_dashboards': user_dashboards.filter(is_published=True).count(),
            'auto_insights_enabled': user_dashboards.filter(auto_insights_enabled=True).count(),
            'interpretability_enabled': user_dashboards.filter(interpretability_enabled=True).count(),
            'total_views': user_dashboards.aggregate(total=Count('view_count'))['total'] or 0,
            'shared_dashboards': DashboardShare.objects.filter(shared_with=user).count(),
        })
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share dashboard with another user."""
        dashboard = self.get_object()
        
        if dashboard.owner != request.user:
            return Response(
                {'error': 'Only the owner can share a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        username = request.data.get('username')
        permission_level = request.data.get('permission_level', 'view')
        expires_at = request.data.get('expires_at')
        
        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            shared_with = User.objects.get(username=username)
            
            # Create or update share
            share, created = DashboardShare.objects.update_or_create(
                dashboard=dashboard,
                shared_with=shared_with,
                defaults={
                    'shared_by': request.user,
                    'permission_level': permission_level,
                    'expires_at': expires_at
                }
            )
            
            serializer = DashboardShareSerializer(share)
            
            return Response({
                'status': 'created' if created else 'updated',
                'share': serializer.data
            })
        
        except User.DoesNotExist:
            return Response(
                {'error': f'User "{username}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """API ViewSet for dashboard widgets."""
    
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter widgets to user's dashboards."""
        return DashboardWidget.objects.filter(
            dashboard__owner=self.request.user
        )
    
    def perform_create(self, serializer):
        """Verify dashboard ownership on widget creation."""
        dashboard = serializer.validated_data['dashboard']
        if dashboard.owner != self.request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def toggle_visibility(self, request, pk=None):
        """Toggle widget visibility."""
        widget = self.get_object()
        widget.is_visible = not widget.is_visible
        widget.save()
        
        return Response({
            'status': 'success',
            'is_visible': widget.is_visible
        })


class DashboardInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for dashboard insights (read-only)."""
    
    serializer_class = DashboardInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter insights to user's dashboards."""
        return DashboardInsight.objects.filter(
            dashboard__owner=self.request.user
        ).order_by('-priority', '-generated_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an insight."""
        insight = self.get_object()
        insight.acknowledge()
        
        serializer = self.get_serializer(insight)
        return Response({
            'status': 'acknowledged',
            'insight': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def actionable(self, request):
        """Get all actionable insights that need attention."""
        insights = self.get_queryset().filter(
            is_actionable=True,
            action_taken=False
        )
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get all critical priority insights."""
        insights = self.get_queryset().filter(priority='critical')
        
        serializer = self.get_serializer(insights, many=True)
        return Response(serializer.data)


class InterpretabilityAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for interpretability analyses (read-only)."""
    
    serializer_class = InterpretabilityAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter analyses to user's dashboards."""
        return InterpretabilityAnalysis.objects.filter(
            dashboard__owner=self.request.user
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get analyses grouped by type."""
        analyses = self.get_queryset()
        
        # Group by analysis type
        grouped = {}
        for analysis in analyses:
            atype = analysis.analysis_type
            if atype not in grouped:
                grouped[atype] = []
            grouped[atype].append(self.get_serializer(analysis).data)
        
        return Response(grouped)
