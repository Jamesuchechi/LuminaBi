"""
Dashboard views for LuminaBI.
Handles dashboard creation, editing, and sharing.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dashboard
from .serializers import DashboardSerializer
from core.views import create_notification


# ============================================================================
# HTML VIEWS
# ============================================================================

class DashboardListView(LoginRequiredMixin, ListView):
    """
    List all dashboards for the current user.
    Shows owned and shared dashboards.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/list.html'
    context_object_name = 'dashboards'
    paginate_by = 20
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Get dashboards owned by or shared with user."""
        user = self.request.user
        return Dashboard.objects.filter(owner=user).order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['total_dashboards'] = Dashboard.objects.filter(owner=user).count()
        context['published_dashboards'] = Dashboard.objects.filter(owner=user, is_published=True).count()
        return context


class DashboardDetailView(LoginRequiredMixin, DetailView):
    """
    Display a single dashboard with all visualizations.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/detail.html'
    context_object_name = 'dashboard'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only show dashboards user owns or has access to."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.get_object()
        context['visualizations'] = dashboard.visualizations.all()
        context['visualization_count'] = dashboard.visualizations.count()
        return context


class DashboardCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new dashboard.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        """Set owner to current user."""
        form.instance.owner = self.request.user
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
        context['page_title'] = 'Create Dashboard'
        return context


class DashboardUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing dashboard.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/form.html'
    fields = ['name', 'description']
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to update."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('dashboards:dashboard_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Dashboard'
        return context


class DashboardDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a dashboard.
    """
    model = Dashboard
    template_name = 'dashboards/dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboards:dashboard_list')
    login_url = 'accounts:login'
    
    def get_queryset(self):
        """Only allow owner to delete."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Delete the dashboard and create notification."""
        obj = self.get_object()
        dashboard_name = obj.name
        response = super().delete(request, *args, **kwargs)
        
        # Create notification
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
# REST API VIEWSETS
# ============================================================================

class DashboardViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Dashboard model.
    Provides CRUD operations and custom actions.
    """
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter dashboards to user's dashboards."""
        return Dashboard.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a dashboard."""
        dashboard = self.get_object()
        dashboard.is_published = True
        dashboard.save()
        return Response({'status': 'dashboard published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a dashboard."""
        dashboard = self.get_object()
        dashboard.is_published = False
        dashboard.save()
        return Response({'status': 'dashboard unpublished'})
    
    @action(detail=True, methods=['post'])
    def add_visualization(self, request, pk=None):
        """Add a visualization to the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            dashboard.visualizations.add(visualization)
            return Response({'status': 'visualization added'})
        except Visualization.DoesNotExist:
            return Response({'error': 'Visualization not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_visualization(self, request, pk=None):
        """Remove a visualization from the dashboard."""
        dashboard = self.get_object()
        visualization_id = request.data.get('visualization_id')
        
        from visualizations.models import Visualization
        
        try:
            visualization = Visualization.objects.get(id=visualization_id)
            dashboard.visualizations.remove(visualization)
            return Response({'status': 'visualization removed'})
        except Visualization.DoesNotExist:
            return Response({'error': 'Visualization not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def update_layout(self, request, pk=None):
        """Update dashboard layout configuration."""
        dashboard = self.get_object()
        layout = request.data.get('layout', {})
        dashboard.layout = layout
        dashboard.save()
        return Response({'status': 'layout updated'})
