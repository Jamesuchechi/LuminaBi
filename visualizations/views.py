"""
Views for visualizations application.
Handles visualization creation, management, and display.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .models import Visualization, VisualizationAccessLog, VisualizationTag, VisualizationComment, VisualizationFavorite
from api.serializers import VisualizationSerializer
from core.mixins import OwnerCheckMixin
from core.views import create_notification


class VisualizationCreateAdvancedView(LoginRequiredMixin, View):
    """New advanced visualization creation view with step-by-step flow."""
    
    template_name = 'visualizations/visualization/create_advanced.html'
    
    def get(self, request):
        """Render the advanced creation template."""
        return render(request, self.template_name, {
            'chart_types': Visualization.CHART_TYPES
        })


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
        
        # Add comments
        context['comments'] = viz.comments.all()
        
        # Add tags
        context['tags'] = viz.tags.all()
        
        # Check if current user has favorited this visualization
        context['is_favorited'] = VisualizationFavorite.objects.filter(
            visualization=viz,
            user=self.request.user
        ).exists()
        
        # Add favorite count
        context['favorite_count'] = viz.favorites.count()
        
        # Log access
        VisualizationAccessLog.objects.create(
            visualization=viz,
            user=self.request.user if self.request.user.is_authenticated else None,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        return context


class VisualizationCreateView(LoginRequiredMixin, CreateView):
    """Create a new visualization."""
    
    model = Visualization
    template_name = 'visualizations/visualization/form.html'
    fields = ['title', 'description', 'chart_type', 'dataset', 'config', 'is_public']
    success_url = reverse_lazy('visualizations:visualization_list')
    
    def form_valid(self, form):
        """Set the owner to the current user and auto-generate config from dataset."""
        form.instance.owner = self.request.user
        
        # Auto-generate config if dataset is selected and config is empty
        if form.instance.dataset and (not form.instance.config or form.instance.config == ''):
            # Generate configuration from dataset
            if form.instance.generate_config_from_dataset():
                message = f'Visualization "{form.instance.title}" created with auto-generated chart configuration.'
            else:
                # Fallback to empty config if generation fails
                form.instance.config = {}
                message = f'Visualization "{form.instance.title}" created. (Configuration generation failed, please configure manually)'
        else:
            # Handle empty config field - convert empty string to empty dict
            if not form.instance.config or form.instance.config == '':
                form.instance.config = {}
            message = f'Visualization "{form.instance.title}" has been created successfully.'
        
        response = super().form_valid(form)
        
        # Create notification
        create_notification(
            user=self.request.user,
            title='Visualization Created',
            message=message,
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
        """Handle config update and auto-generation if dataset changed."""
        # If dataset changed and config is empty, auto-generate
        if form.instance.dataset:
            if (not form.instance.config or form.instance.config == '' or 
                'regenerate' in self.request.POST):
                form.instance.generate_config_from_dataset()
            # Also handle if just config field is empty
            elif not form.instance.config or form.instance.config == '':
                form.instance.config = {}
        else:
            # No dataset, ensure config is dict
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
    
    @action(detail=True, methods=['post'])
    def generate_config(self, request, pk=None):
        """
        Automatically generate chart configuration from the linked dataset.
        Called when user selects a dataset or changes chart type.
        """
        visualization = self.get_object()
        if visualization.owner != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not visualization.dataset:
            return Response(
                {'error': 'No dataset linked to this visualization'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            success = visualization.generate_config_from_dataset()
            
            if success:
                visualization.save()
                return Response({
                    'status': 'success',
                    'message': 'Configuration generated successfully',
                    'config': visualization.config,
                    'chart_type': visualization.chart_type,
                })
            else:
                return Response(
                    {'error': 'Failed to generate configuration from dataset'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Configuration generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
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


@csrf_exempt
@login_required
def preview_config_direct(request):
    """Direct POST endpoint for generating preview config (fallback safe).

    This view mirrors the DRF action but is registered separately to avoid
    routing/OPTIONS issues observed in some environments. It always returns
    a minimal Chart.js configuration so the frontend can render a chart.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    dataset_id = payload.get('dataset_id')
    chart_type = payload.get('chart_type', 'bar')
    title = payload.get('title', 'Chart')

    if not dataset_id:
        return JsonResponse({'error': 'dataset_id is required'}, status=400)

    try:
        from datasets.models import Dataset
        from .config_generator import ChartConfigGenerator
        from datasets.services import FileParser
        import os

        dataset = Dataset.objects.get(id=dataset_id, owner=request.user)

        if not os.path.exists(dataset.file.path):
            return JsonResponse({'error': 'Dataset file not found'}, status=404)

        df = FileParser.parse_file(dataset.file.path, dataset.file_type)

        # Attempt to use the main generator
        generator = ChartConfigGenerator(df, getattr(dataset, 'column_names', None))
        try:
            config = generator.generate_config(chart_type=chart_type, title=title)
        except Exception:
            config = None

        # If generator produced an unusable config (no datasets), create a fallback
        def make_fallback(df, chart_type, title):
            labels = []
            datasets = []
            # Prefer categorical labels + numeric values for most charts
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

            if chart_type in ['pie', 'donut']:
                # Need labels and single numeric
                if categorical_cols and numeric_cols:
                    labels = df[categorical_cols[0]].astype(str).tolist()
                    values = df[numeric_cols[0]].fillna(0).tolist()
                    datasets = [{
                        'label': str(numeric_cols[0]),
                        'data': values,
                        'backgroundColor': ChartConfigGenerator(df).column_names if False else [],
                    }]
                elif numeric_cols:
                    labels = [str(i) for i in range(len(df))]
                    values = df[numeric_cols[0]].fillna(0).tolist()
                    datasets = [{
                        'label': str(numeric_cols[0]),
                        'data': values,
                        'backgroundColor': [],
                    }]
                else:
                    labels = [str(i) for i in range(len(df))]
                    datasets = [{
                        'label': 'values',
                        'data': [1 for _ in range(len(df))],
                        'backgroundColor': [],
                    }]
                return {
                    'type': 'pie',
                    'data': {'labels': labels, 'datasets': datasets},
                    'options': {'plugins': {'title': {'display': True, 'text': title}}}
                }

            # For bar/line/scatter/etc.
            if numeric_cols:
                x_labels = df.index.astype(str).tolist()
                y_col = numeric_cols[0]
                datasets = [{
                    'label': str(y_col),
                    'data': df[y_col].fillna(0).tolist(),
                    'borderColor': '#00f3ff',
                    'backgroundColor': 'rgba(0,243,255,0.4)'
                }]
                return {
                    'type': 'line' if chart_type == 'line' else ('bar' if chart_type == 'bar' else 'line'),
                    'data': {'labels': x_labels, 'datasets': datasets},
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'plugins': {'title': {'display': True, 'text': title}},
                    }
                }

            # If no numeric columns at all, produce a simple categorical count
            if categorical_cols:
                col = categorical_cols[0]
                counts = df[col].astype(str).value_counts()
                labels = counts.index.tolist()
                values = counts.tolist()
                datasets = [{
                    'label': str(col),
                    'data': values,
                    'backgroundColor': 'rgba(189,0,255,0.6)'
                }]
                return {
                    'type': 'bar',
                    'data': {'labels': labels, 'datasets': datasets},
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'title': {'display': True, 'text': title}}}
                }

            # Final fallback: tiny dataset
            return {
                'type': 'bar',
                'data': {'labels': [str(i) for i in range(min(5, len(df)))], 'datasets': [{'label': 'values', 'data': [1 for _ in range(min(5, len(df)))]}]},
                'options': {'plugins': {'title': {'display': True, 'text': title}}}
            }

        if not config or (isinstance(config, dict) and config.get('data', {}).get('datasets') == []):
            try:
                config = make_fallback(df, chart_type, title)
            except Exception as e:
                return JsonResponse({'error': f'Failed to generate preview: {str(e)}'}, status=500)

        return JsonResponse({'status': 'success', 'config': config, 'chart_type': chart_type}, status=200)

    except Dataset.DoesNotExist:
        return JsonResponse({'error': 'Dataset not found or you do not have permission to access it'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to generate preview: {str(e)}'}, status=500)


# ============================================================================
# COMMENT MANAGEMENT VIEWS
# ============================================================================

class CommentCreateView(LoginRequiredMixin, View):
    """Create a comment on a visualization."""
    
    def post(self, request, pk):
        """Create a new comment."""
        visualization = get_object_or_404(Visualization, pk=pk)
        
        # Check if user can view this visualization
        if visualization.owner != request.user and not visualization.is_public:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Comment content is required'}, status=400)
        
        comment = VisualizationComment.objects.create(
            visualization=visualization,
            user=request.user,
            content=content
        )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'user': comment.user.username,
                    'user_full_name': comment.user.get_full_name() or comment.user.username,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                }
            })
        
        return redirect('visualizations:visualization_detail', pk=visualization.pk)


class CommentDeleteView(LoginRequiredMixin, View):
    """Delete a comment."""
    
    def post(self, request, pk, comment_id):
        """Delete a comment."""
        comment = get_object_or_404(VisualizationComment, pk=comment_id)
        
        # Only comment owner or visualization owner can delete
        if comment.user != request.user and comment.visualization.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        visualization_pk = comment.visualization.pk
        comment.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Comment deleted'})
        
        return redirect('visualizations:visualization_detail', pk=visualization_pk)


# ============================================================================
# TAG MANAGEMENT VIEWS
# ============================================================================

class TagAddView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Add a tag to a visualization."""
    
    def post(self, request, pk):
        """Add a tag."""
        visualization = get_object_or_404(Visualization, pk=pk)
        self.check_owner(visualization, request.user)
        
        tag_name = request.POST.get('name', '').strip().lower()
        if not tag_name:
            return JsonResponse({'error': 'Tag name is required'}, status=400)
        
        # Create or get tag
        tag, created = VisualizationTag.objects.get_or_create(
            visualization=visualization,
            name=tag_name
        )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                },
                'created': created
            })
        
        return redirect('visualizations:visualization_detail', pk=visualization.pk)


class TagRemoveView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Remove a tag from a visualization."""
    
    def post(self, request, pk, tag_id):
        """Remove a tag."""
        tag = get_object_or_404(VisualizationTag, pk=tag_id)
        visualization = tag.visualization
        self.check_owner(visualization, request.user)
        
        tag.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Tag removed'})
        
        return redirect('visualizations:visualization_detail', pk=visualization.pk)


# ============================================================================
# FAVORITE MANAGEMENT VIEWS
# ============================================================================

class FavoriteToggleView(LoginRequiredMixin, View):
    """Toggle favorite status for a visualization."""
    
    def post(self, request, pk):
        """Toggle favorite."""
        visualization = get_object_or_404(Visualization, pk=pk)
        
        # Check if user can view this visualization
        if visualization.owner != request.user and not visualization.is_public:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        favorite, created = VisualizationFavorite.objects.get_or_create(
            visualization=visualization,
            user=request.user
        )
        
        if not created:
            # Already favorited, remove it
            favorite.delete()
            is_favorited = False
        else:
            is_favorited = True
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'is_favorited': is_favorited,
                'message': 'Added to favorites' if is_favorited else 'Removed from favorites'
            })
        
        return redirect('visualizations:visualization_detail', pk=visualization.pk)

