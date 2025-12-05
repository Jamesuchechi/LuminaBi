"""
Views for datasets application.
Handles dataset management, file uploads, and data processing.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Dataset
from api.serializers import DatasetSerializer
from core.mixins import OwnerCheckMixin


class DatasetListView(LoginRequiredMixin, ListView):
    """List datasets owned by the current user."""
    
    model = Dataset
    template_name = 'datasets/dataset/list.html'
    context_object_name = 'datasets'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter datasets to user's datasets."""
        return Dataset.objects.filter(owner=self.request.user).order_by('-uploaded_at')
    
    def get_context_data(self, **kwargs):
        """Add statistics and metadata to context."""
        context = super().get_context_data(**kwargs)
        datasets = self.get_queryset()
        
        context['statistics'] = {
            'total_datasets': datasets.count(),
            'total_size_mb': sum([
                default_storage.size(d.file.name) / (1024 * 1024) if d.file else 0
                for d in datasets
            ]),
            'cleaned_datasets': datasets.filter(is_cleaned=True).count(),
        }
        
        return context


class DatasetDetailView(LoginRequiredMixin, OwnerCheckMixin, DetailView):
    """Display dataset details and metadata."""
    
    model = Dataset
    template_name = 'datasets/dataset/detail.html'
    context_object_name = 'dataset'
    
    def get_object(self):
        """Get the dataset and verify ownership."""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj
    
    def get_context_data(self, **kwargs):
        """Add file preview and visualizations to context."""
        context = super().get_context_data(**kwargs)
        dataset = self.get_object()
        
        # Add file info
        if dataset.file:
            context['file_size_mb'] = dataset.file.size / (1024 * 1024)
        
        # Add visualizations using this dataset
        context['visualizations'] = dataset.visualizations.all()
        
        return context


class DatasetCreateView(LoginRequiredMixin, CreateView):
    """Upload a new dataset."""
    
    model = Dataset
    template_name = 'datasets/dataset/form.html'
    fields = ['name', 'description', 'file']
    success_url = reverse_lazy('datasets:dataset_list')
    
    def form_valid(self, form):
        """Set the owner to the current user."""
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add form title for clarity."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Upload New Dataset'
        context['button_text'] = 'Upload Dataset'
        return context


class DatasetUpdateView(LoginRequiredMixin, OwnerCheckMixin, UpdateView):
    """Update dataset metadata."""
    
    model = Dataset
    template_name = 'datasets/dataset/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('datasets:dataset_list')
    
    def get_object(self):
        """Get the dataset and verify ownership."""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj
    
    def get_context_data(self, **kwargs):
        """Add form title for clarity."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Dataset'
        context['button_text'] = 'Save Changes'
        return context


class DatasetDeleteView(LoginRequiredMixin, OwnerCheckMixin, DeleteView):
    """Delete a dataset."""
    
    model = Dataset
    template_name = 'datasets/dataset/confirm_delete.html'
    success_url = reverse_lazy('datasets:dataset_list')
    
    def get_object(self):
        """Get the dataset and verify ownership."""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj


class DatasetCleaningView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Handle dataset cleaning operations."""
    
    def post(self, request, pk):
        """Mark dataset as cleaned or perform cleaning operations."""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        action = request.POST.get('action', 'mark_cleaned')
        
        if action == 'mark_cleaned':
            dataset.is_cleaned = True
            dataset.save()
            message = 'Dataset marked as cleaned.'
        else:
            # Could implement actual cleaning logic here
            message = 'Cleaning operation performed.'
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': message})
        
        return redirect('dataset_detail', pk=dataset.pk)


class DatasetPreviewView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Preview dataset contents."""
    
    def get(self, request, pk):
        """Return a preview of the dataset."""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        preview_data = {
            'name': dataset.name,
            'description': dataset.description,
            'row_count': dataset.row_count,
            'col_count': dataset.col_count,
            'is_cleaned': dataset.is_cleaned,
            'metadata': dataset.metadata,
        }
        
        return JsonResponse(preview_data)


class DatasetExportView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Export dataset in various formats."""
    
    def get(self, request, pk):
        """Export dataset."""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        file_format = request.GET.get('format', 'csv')
        
        if not dataset.file:
            return JsonResponse({'error': 'No file available'}, status=404)
        
        # Could implement export logic here
        return JsonResponse({
            'status': 'export_initiated',
            'format': file_format,
            'dataset_id': dataset.id
        })


# ============================================================================
# REST API VIEWSETS
# ============================================================================

class DatasetViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Dataset model.
    Provides CRUD operations and dataset management.
    """
    serializer_class = DatasetSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter datasets to user's datasets."""
        return Dataset.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_cleaned(self, request, pk=None):
        """Mark a dataset as cleaned."""
        dataset = self.get_object()
        dataset.is_cleaned = True
        dataset.save()
        return Response({'status': 'dataset marked as cleaned'})
    
    @action(detail=True, methods=['post'])
    def update_metadata(self, request, pk=None):
        """Update dataset metadata."""
        dataset = self.get_object()
        metadata = request.data.get('metadata', {})
        dataset.metadata.update(metadata)
        dataset.save()
        return Response({'status': 'metadata updated', 'metadata': dataset.metadata})
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Get a preview of the dataset."""
        dataset = self.get_object()
        return Response({
            'name': dataset.name,
            'description': dataset.description,
            'row_count': dataset.row_count,
            'col_count': dataset.col_count,
            'is_cleaned': dataset.is_cleaned,
            'metadata': dataset.metadata,
            'visualizations_count': dataset.visualizations.count(),
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about user's datasets."""
        datasets = self.get_queryset()
        return Response({
            'total_datasets': datasets.count(),
            'cleaned_datasets': datasets.filter(is_cleaned=True).count(),
            'total_size_bytes': sum([
                default_storage.size(d.file.name) if d.file else 0
                for d in datasets
            ]),
        })


