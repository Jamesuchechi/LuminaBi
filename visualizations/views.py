"""
Views for visualizations application.
Handles visualization creation, management, and display.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Visualization
from api.serializers import VisualizationSerializer
from core.mixins import OwnerCheckMixin
from core.views import create_notification


class VisualizationListView(LoginRequiredMixin, ListView):
    """List visualizations owned by the current user."""
    
    model = Visualization
    template_name = 'visualizations/visualization/list.html'
    context_object_name = 'visualizations'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter visualizations to user's visualizations."""
        return Visualization.objects.filter(
            Q(owner=self.request.user) | Q(is_public=True)
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add statistics to context."""
        context = super().get_context_data(**kwargs)
        user_viz = Visualization.objects.filter(owner=self.request.user)
        
        # Build chart_types statistics
        chart_types = {}
        if user_viz.exists():
            for chart_type, label in Visualization.CHART_TYPES:
                count = user_viz.filter(chart_type=chart_type).count()
                if count > 0:
                    chart_types[label] = count
        
        context['statistics'] = {
            'total_visualizations': user_viz.count(),
            'public_visualizations': user_viz.filter(is_public=True).count(),
            'chart_types': chart_types
        }
        
        return context


class VisualizationDetailView(LoginRequiredMixin, DetailView):
    """Display visualization details and configuration."""
    
    model = Visualization
    template_name = 'visualizations/visualization/detail.html'
    context_object_name = 'visualization'
    
    def get_object(self):
        """Get visualization - allow viewing public visualizations."""
        obj = super().get_object()
        if obj.owner != self.request.user and not obj.is_public:
            self.check_owner(obj, self.request.user)
        return obj
    
    def get_context_data(self, **kwargs):
        """Add chart configuration and related data."""
        context = super().get_context_data(**kwargs)
        viz = self.get_object()
        
        context['is_owner'] = viz.owner == self.request.user
        context['can_edit'] = context['is_owner']
        
        return context


class VisualizationCreateView(LoginRequiredMixin, CreateView):
    """Create a new visualization."""
    
    model = Visualization
    template_name = 'visualizations/visualization/form.html'
    fields = ['title', 'description', 'chart_type', 'dataset', 'config', 'is_public']
    success_url = reverse_lazy('visualizations:visualization_list')
    
    def form_valid(self, form):
        """Set the owner to the current user and handle empty config."""
        form.instance.owner = self.request.user
        # Handle empty config field - convert empty string to empty dict
        if not form.instance.config or form.instance.config == '':
            form.instance.config = {}
        response = super().form_valid(form)
        
        # Create notification
        create_notification(
            user=self.request.user,
            title='Visualization Created',
            message=f'Visualization "{form.instance.title}" has been created successfully.',
            notification_type='success',
            related_app='visualizations',
            related_model='Visualization',
            related_object_id=form.instance.id
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        """Add form title and chart type choices."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Visualization'
        context['button_text'] = 'Create Visualization'
        context['chart_types'] = Visualization.CHART_TYPES
        return context


class VisualizationUpdateView(LoginRequiredMixin, OwnerCheckMixin, UpdateView):
    """Update visualization details and configuration."""
    
    model = Visualization
    template_name = 'visualizations/visualization/form.html'
    fields = ['title', 'description', 'chart_type', 'dataset', 'config', 'is_public']
    success_url = reverse_lazy('visualizations:visualization_list')
    
    def get_object(self):
        """Get visualization and verify ownership."""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj
    
    def form_valid(self, form):
        """Handle empty config field - convert empty string to empty dict."""
        if not form.instance.config or form.instance.config == '':
            form.instance.config = {}
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add form title for clarity."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Visualization'
        context['button_text'] = 'Save Changes'
        context['chart_types'] = Visualization.CHART_TYPES
        return context


class VisualizationDeleteView(LoginRequiredMixin, OwnerCheckMixin, DeleteView):
    """Delete a visualization."""
    
    model = Visualization
    template_name = 'visualizations/visualization/confirm_delete.html'
    success_url = reverse_lazy('visualizations:visualization_list')
    
    def get_object(self):
        """Get visualization and verify ownership."""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj
    
    def delete(self, request, *args, **kwargs):
        """Delete the visualization and create notification."""
        obj = self.get_object()
        viz_title = obj.title
        response = super().delete(request, *args, **kwargs)
        
        # Create notification
        create_notification(
            user=request.user,
            title='Visualization Deleted',
            message=f'Visualization "{viz_title}" has been deleted.',
            notification_type='info',
            related_app='visualizations',
            related_model='Visualization'
        )
        
        return response


class VisualizationPublishView(LoginRequiredMixin, OwnerCheckMixin, DetailView):
    """Toggle visualization public/private status."""
    
    model = Visualization
    
    def post(self, request, pk):
        """Toggle public status."""
        viz = self.get_object()
        self.check_owner(viz, request.user)
        
        action = request.POST.get('action', 'toggle')
        
        if action == 'publish':
            viz.is_public = True
        elif action == 'unpublish':
            viz.is_public = False
        else:
            viz.is_public = not viz.is_public
        
        viz.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'is_public': viz.is_public,
                'message': 'Published' if viz.is_public else 'Unpublished'
            })
        
        return redirect('visualization_detail', pk=viz.pk)


class VisualizationPreviewView(LoginRequiredMixin, DetailView):
    """Preview visualization with current data."""
    
    model = Visualization
    
    def get(self, request, pk):
        """Return visualization configuration for rendering."""
        viz = get_object_or_404(Visualization, pk=pk)
        
        if viz.owner != request.user and not viz.is_public:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        return JsonResponse({
            'id': viz.id,
            'title': viz.title,
            'chart_type': viz.chart_type,
            'config': viz.config,
            'dataset_id': viz.dataset.id if viz.dataset else None,
            'is_public': viz.is_public,
        })


# ============================================================================
# REST API VIEWSETS
# ============================================================================

class VisualizationViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Visualization model.
    Provides CRUD operations and visualization management.
    """
    serializer_class = VisualizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter visualizations - user's and public ones."""
        return Visualization.objects.filter(
            Q(owner=self.request.user) | Q(is_public=True)
        )
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    def perform_update(self, serializer):
        """Verify ownership on update."""
        if serializer.instance.owner != self.request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Make visualization public."""
        visualization = self.get_object()
        if visualization.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        visualization.is_public = True
        visualization.save()
        return Response({'status': 'visualization published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Make visualization private."""
        visualization = self.get_object()
        if visualization.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        visualization.is_public = False
        visualization.save()
        return Response({'status': 'visualization unpublished'})
    
    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        """Update visualization configuration."""
        visualization = self.get_object()
        if visualization.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        config = request.data.get('config', {})
        visualization.config.update(config)
        visualization.save()
        return Response({
            'status': 'configuration updated',
            'config': visualization.config
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about user's visualizations."""
        user_viz = Visualization.objects.filter(owner=request.user)
        chart_type_counts = {}
        for chart_type, display_name in Visualization.CHART_TYPES:
            chart_type_counts[chart_type] = user_viz.filter(chart_type=chart_type).count()
        
        return Response({
            'total_visualizations': user_viz.count(),
            'public_visualizations': user_viz.filter(is_public=True).count(),
            'by_chart_type': chart_type_counts,
        })

