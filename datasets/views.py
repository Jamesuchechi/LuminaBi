"""
Complete File Intelligence, Data Analysis, Cleaning, and Visualization System
Views for datasets application
"""

import os
import json
import logging
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Q, Count, Avg, Sum, F
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    Dataset, DatasetVersion, FileAnalysis, CleaningOperation,
    FILE_TYPE_CHOICES, OPERATION_TYPE_CHOICES
)
from .services import FileParser, FileAnalyzer, DataCleaner, FileExporter
from visualizations.models import Visualization
from api.serializers import DatasetSerializer
from core.mixins import OwnerCheckMixin
from core.views import create_notification

logger = logging.getLogger(__name__)

try:
    from .visualization_service import VisualizationEngine
except ImportError:
    logger.warning("VisualizationEngine not available - plotly not installed")
    VisualizationEngine = None

logger = logging.getLogger(__name__)


# ============================================================================
# FILE UPLOAD AND ANALYSIS
# ============================================================================

class DatasetUploadView(LoginRequiredMixin, CreateView):
    """
    Handle file upload with drag & drop support.
    Automatically analyzes file after upload.
    """
    model = Dataset
    template_name = 'datasets/dataset/upload.html'
    fields = ['name', 'description', 'file']
    success_url = reverse_lazy('datasets:dataset_list')

    def form_valid(self, form):
        """Process uploaded file and analyze it"""
        form.instance.owner = self.request.user
        
        # Detect file type
        file_name = form.instance.file.name
        file_type = FileParser.detect_file_type(file_name)
        form.instance.file_type = file_type
        form.instance.file_size = form.instance.file.size
        
        response = super().form_valid(form)
        dataset = self.object
        
        # Analyze the file
        try:
            self._analyze_dataset(dataset)
            message = f'Dataset "{dataset.name}" uploaded and analyzed successfully.'
            msg_type = 'success'
        except Exception as e:
            logger.error(f"Error analyzing dataset {dataset.id}: {str(e)}")
            message = f'Dataset uploaded but analysis failed: {str(e)}'
            msg_type = 'warning'
        
        # Create notification
        create_notification(
            user=self.request.user,
            title='Dataset Uploaded',
            message=message,
            notification_type=msg_type,
            related_app='datasets',
            related_model='Dataset',
            related_object_id=dataset.id
        )
        
        return response

    def _analyze_dataset(self, dataset: Dataset):
        """Analyze uploaded dataset"""
        file_path = dataset.file.path
        
        # Parse file
        df = FileParser.parse_file(file_path, dataset.file_type)
        
        # Run analysis
        analyzer = FileAnalyzer(df)
        analysis = analyzer.analyze()
        
        # Store results in dataset
        dataset.row_count = len(df)
        dataset.col_count = len(df.columns)
        dataset.column_names = list(df.columns)
        dataset.is_analyzed = True
        dataset.data_quality_score = analysis['data_quality_score']
        dataset.summary = analysis['summary']
        
        # Store empty cells info
        empty_cells_data = analysis['empty_cells']
        dataset.empty_rows_count = empty_cells_data['total_empty_rows']
        dataset.empty_cols_count = empty_cells_data['total_empty_columns']
        dataset.empty_cells = empty_cells_data['empty_cells']
        
        # Store duplicates info
        duplicates_data = analysis['duplicates']
        dataset.duplicate_rows = duplicates_data['duplicate_row_indices']
        dataset.duplicate_values = duplicates_data['duplicate_values_by_column']
        
        dataset.analysis_metadata = analysis
        dataset.save()
        
        # Create FileAnalysis record
        FileAnalysis.objects.update_or_create(
            dataset=dataset,
            defaults={
                'analysis_data': analysis,
                'empty_cells_detail': empty_cells_data['empty_cells'],
                'column_stats': analysis['column_stats'],
                'data_types': analysis['data_types'],
                'missing_values': analysis['missing_values'],
                'outliers': analysis['outliers'],
            }
        )
        
        # Create initial version
        DatasetVersion.objects.create(
            dataset=dataset,
            file=dataset.file,
            version_number=1,
            operation_type='upload',
            operation_description=f'Initial upload: {dataset.file_type}',
            metadata={'file_size': dataset.file_size, 'file_type': dataset.file_type},
            rows_before=0,
            rows_after=len(df),
            is_current=True,
        )

    def get_context_data(self, **kwargs):
        """Add upload info to context"""
        context = super().get_context_data(**kwargs)
        context['supported_formats'] = ['CSV', 'Excel (xlsx/xls)', 'JSON', 'PDF', 'Text']
        return context


class DatasetListView(LoginRequiredMixin, ListView):
    """
    List all datasets owned by user with summary statistics.
    Includes search, filtering, and sorting capabilities.
    """
    model = Dataset
    template_name = 'datasets/dataset/list.html'
    context_object_name = 'datasets'
    paginate_by = 20

    def get_queryset(self):
        """Filter datasets to user's datasets"""
        queryset = Dataset.objects.filter(owner=self.request.user).order_by('-uploaded_at')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'analyzed':
            queryset = queryset.filter(is_analyzed=True)
        elif status_filter == 'cleaned':
            queryset = queryset.filter(is_cleaned=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Add statistics to context"""
        context = super().get_context_data(**kwargs)
        datasets = self.get_queryset()
        
        context['statistics'] = {
            'total_datasets': datasets.count(),
            'analyzed_datasets': datasets.filter(is_analyzed=True).count(),
            'cleaned_datasets': datasets.filter(is_cleaned=True).count(),
            'total_visualizations': Visualization.objects.filter(
                dataset__owner=self.request.user
            ).count(),
            'avg_quality_score': datasets.aggregate(
                avg_score=Avg('data_quality_score')
            )['avg_score'] or 0,
        }
        
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        return context


class DatasetDetailView(LoginRequiredMixin, OwnerCheckMixin, DetailView):
    """
    Display comprehensive dataset details including:
    - File analysis results
    - Data quality score
    - Empty cells, duplicates
    - Version history
    - Associated visualizations
    """
    model = Dataset
    template_name = 'datasets/dataset/detail.html'
    context_object_name = 'dataset'

    def get_object(self):
        """Get dataset and verify ownership"""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        """Add analysis, versions, and visualizations to context"""
        context = super().get_context_data(**kwargs)
        dataset = self.get_object()
        
        # File analysis
        try:
            analysis = FileAnalysis.objects.get(dataset=dataset)
            context['analysis'] = analysis
            context['empty_cells'] = analysis.empty_cells_detail[:50]  # First 50
            context['duplicates'] = analysis.duplicate_rows_detail[:50]
            
            # Extract analysis data
            analysis_data = analysis.analysis_data
            if analysis_data:
                # Basic stats
                if 'basic_stats' in analysis_data:
                    basic = analysis_data['basic_stats']
                    context['row_count'] = basic.get('rows', 0)
                    context['col_count'] = basic.get('columns', 0)
                
                # Empty cells
                if 'empty_cells' in analysis_data:
                    empty = analysis_data['empty_cells']
                    context['empty_cell_count'] = empty.get('total_empty_cells', 0)
                
                # Duplicates
                if 'duplicates' in analysis_data:
                    dups = analysis_data['duplicates']
                    context['duplicate_row_count'] = dups.get('total_duplicate_rows', 0)
                
        except FileAnalysis.DoesNotExist:
            context['analysis'] = None
            context['row_count'] = dataset.row_count or 0
            context['col_count'] = dataset.col_count or 0
        
        # Version history
        context['versions'] = dataset.versions.all().order_by('-version_number')
        context['current_version'] = dataset.versions.filter(is_current=True).first()
        
        # Visualizations
        context['visualizations'] = dataset.visualizations.all()
        
        # Cleaning operations
        context['cleaning_operations'] = dataset.cleaning_operations.all()[:10]
        
        # File preview (first 100 rows)
        try:
            df = FileParser.parse_file(dataset.file.path, dataset.file_type)
            preview_df = df.head(100)
            context['file_preview'] = preview_df.to_html(classes='table table-striped', index=False)
            context['preview_rows'] = min(100, len(df))
            context['total_rows'] = len(df)
        except Exception as e:
            logger.error(f"Error creating file preview: {str(e)}")
            context['file_preview'] = None
        
        return context

class DatasetAnalysisView(LoginRequiredMixin, OwnerCheckMixin, DetailView):
    """
    Display detailed analysis results with tabs for:
    - Summary
    - Empty Cells
    - Duplicates
    - Column Statistics
    - Data Quality
    """
    model = Dataset
    template_name = 'datasets/dataset/analysis.html'
    context_object_name = 'dataset'

    def get_object(self):
        """Get dataset and verify ownership"""
        obj = super().get_object()
        self.check_owner(obj, self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        """Add detailed analysis to context"""
        context = super().get_context_data(**kwargs)
        dataset = self.get_object()
        
        try:
            analysis = FileAnalysis.objects.get(dataset=dataset)
            context['analysis'] = analysis
            context['has_analysis'] = True
            
            # Parse analysis data for template
            analysis_data = analysis.analysis_data or {}
            
            # Add basic stats
            basic_stats = analysis_data.get('basic_stats', {})
            context['analysis_summary'] = {
                'row_count': basic_stats.get('rows', dataset.row_count or 0),
                'column_count': basic_stats.get('columns', dataset.col_count or 0),
            }
            
            # Add data quality score
            context['data_quality_score'] = analysis_data.get('data_quality_score', dataset.data_quality_score or 0)
            context['summary_text'] = analysis_data.get('summary', dataset.summary or '')
            
            # FIXED: Add empty cells info with proper counts
            empty_cells_data = analysis_data.get('empty_cells', {})
            context['empty_cell_count'] = empty_cells_data.get('total_empty_cells', 0)
            context['empty_cells'] = empty_cells_data.get('empty_cells', [])[:100]
            
            # FIXED: Add duplicates info with proper counts
            duplicates_data = analysis_data.get('duplicates', {})
            context['duplicate_count'] = duplicates_data.get('total_duplicate_rows', 0)
            context['duplicates'] = duplicates_data.get('duplicate_row_indices', [])[:100]
            
            # FIXED: Add outliers with proper formatting
            outliers_list = analysis_data.get('outliers', [])
            context['outlier_count'] = sum(outlier.get('count', 0) for outlier in outliers_list if isinstance(outlier, dict))
            
            # Format outliers for template
            context['outliers'] = {}
            for outlier in outliers_list:
                if isinstance(outlier, dict) and 'column' in outlier:
                    col = outlier['column']
                    context['outliers'][col] = {
                        'count': outlier.get('count', 0),
                        'bounds': outlier.get('bounds', {}),
                        'sample_values': outlier.get('sample_values', [])[:5]
                    }
            
            # Add column statistics
            column_stats = analysis_data.get('column_stats', analysis.column_stats or {})
            context['column_statistics'] = {}
            for col_name, stats in column_stats.items():
                context['column_statistics'][col_name] = {
                    'dtype': stats.get('dtype', 'Unknown'),
                    'non_null': stats.get('non_null_count', 0),
                    'unique': stats.get('unique_count', 0),
                    'min': stats.get('min'),
                    'max': stats.get('max'),
                    'mean': stats.get('mean'),
                    'median': stats.get('median'),
                    'std': stats.get('std'),
                }
            
            # Add missing values per column
            context['missing_values'] = analysis_data.get('missing_values', analysis.missing_values or {})
            
            # Add file size in MB for display
            if dataset.file_size:
                context['file_size_mb'] = dataset.file_size / (1024 * 1024)
            
        except FileAnalysis.DoesNotExist:
            # If no analysis exists, provide defaults
            context['has_analysis'] = False
            context['analysis_summary'] = {
                'row_count': dataset.row_count or 0,
                'column_count': dataset.col_count or 0,
            }
            context['data_quality_score'] = dataset.data_quality_score or 0
            context['summary_text'] = dataset.summary or 'No analysis available yet.'
            context['empty_cell_count'] = 0
            context['empty_cells'] = []
            context['duplicate_count'] = 0
            context['duplicates'] = []
            context['outlier_count'] = 0
            context['outliers'] = {}
            context['column_statistics'] = {}
            context['missing_values'] = {}
        
        return context


class FileViewerView(LoginRequiredMixin, OwnerCheckMixin, View):
    """
    Render file with pagination and formatting.
    Supports switching between versions.
    """
    
    def get(self, request, pk):
        """Display file with pagination"""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        # Get version to display
        version_id = request.GET.get('version_id')
        if version_id:
            version = get_object_or_404(DatasetVersion, id=version_id, dataset=dataset)
            file_path = version.file.path
        else:
            file_path = dataset.file.path
        
        # Parse file
        try:
            df = FileParser.parse_file(file_path, dataset.file_type)
        except Exception as e:
            return render(request, 'datasets/dataset/viewer_error.html', {
                'error': f"Could not parse file: {str(e)}"
            })
        
        # Pagination
        page_num = request.GET.get('page', 1)
        rows_per_page = request.GET.get('rows_per_page', 50)
        
        # Support 'all' option
        if rows_per_page == 'all':
            rows_per_page_int = len(df)
        else:
            rows_per_page_int = int(rows_per_page)
        
        paginator = Paginator(df.values.tolist(), rows_per_page_int)
        try:
            page = paginator.page(page_num)
        except:
            page = paginator.page(1)
        
        # Format data - convert to list of dicts for better template handling
        columns = list(df.columns)
        rows = []
        for row_data in page.object_list:
            row_dict = {col: val for col, val in zip(columns, row_data)}
            rows.append(row_dict)
        
        # Get all versions for switching
        versions = dataset.versions.all()
        
        context = {
            'dataset': dataset,
            'current_version_id': version_id,
            'columns': columns,
            'rows': rows,
            'page': page,
            'rows_per_page': rows_per_page,
            'all_rows_count': len(df),
            'versions': versions,
            'current_file': f"v{version.version_number}" if version_id else "Original",
        }
        
        return render(request, 'datasets/dataset/viewer.html', context)


# ============================================================================
# DATA CLEANING OPERATIONS
# ============================================================================

class RemoveDuplicatesView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Remove duplicate rows and create new version"""
    
    def post(self, request, pk):
        """Process duplicate removal"""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        # Get latest version
        version = dataset.versions.filter(is_current=True).first()
        if not version:
            return JsonResponse({'error': 'No current version found'}, status=400)
        
        try:
            # Parse current file
            df = FileParser.parse_file(version.file.path, dataset.file_type)
            
            # Remove duplicates
            cleaner = DataCleaner()
            df_cleaned, result = cleaner.remove_duplicates(df)
            
            # Save new version
            new_version_num = dataset.versions.count() + 1
            temp_file = self._save_to_temp(df_cleaned, dataset.file_type)
            
            with open(temp_file, 'rb') as f:
                new_version = DatasetVersion.objects.create(
                    dataset=dataset,
                    version_number=new_version_num,
                    operation_type='deduplicate',
                    operation_description=f"Removed {result['duplicates_removed']} duplicate rows",
                    rows_before=result['rows_before'],
                    rows_after=result['rows_after'],
                    changes_made=result,
                )
                new_version.file.save(
                    f"{dataset.name}_v{new_version_num}.csv",
                    ContentFile(f.read())
                )
            
            # Create cleaning operation record
            CleaningOperation.objects.create(
                dataset=dataset,
                operation_type='deduplicate',
                created_by_version=new_version,
                result=result,
                status='success',
            )
            
            # Mark old version as not current
            version.is_current = False
            version.save()
            new_version.is_current = True
            new_version.save()
            
            create_notification(
                user=request.user,
                title='Duplicates Removed',
                message=f"Removed {result['duplicates_removed']} duplicate rows. New version created.",
                notification_type='success',
                related_app='datasets',
                related_model='Dataset',
                related_object_id=dataset.id
            )
            
            return JsonResponse({
                'status': 'success',
                'duplicates_removed': result['duplicates_removed'],
                'rows_before': result['rows_before'],
                'rows_after': result['rows_after'],
                'new_version_id': new_version.id,
            })
        
        except Exception as e:
            logger.error(f"Error removing duplicates: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    @staticmethod
    def _save_to_temp(df, file_type):
        """Save DataFrame to temporary file"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.csv' if file_type == 'csv' else '.xlsx',
            delete=False
        )
        
        if file_type == 'csv' or file_type == 'text':
            df.to_csv(temp_file.name, index=False)
        elif file_type == 'excel':
            df.to_excel(temp_file.name, index=False)
        
        return temp_file.name


class FillEmptyCellsView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Fill empty cells with specified values"""
    
    def post(self, request, pk):
        """Process filling empty cells"""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        version = dataset.versions.filter(is_current=True).first()
        if not version:
            return JsonResponse({'error': 'No current version found'}, status=400)
        
        try:
            data = json.loads(request.body)
            cells_to_fill = data.get('cells_to_fill', {})
            
            df = FileParser.parse_file(version.file.path, dataset.file_type)
            
            cleaner = DataCleaner()
            df_filled, result = cleaner.fill_empty_cells_by_address(df, cells_to_fill)
            
            # Save new version
            new_version_num = dataset.versions.count() + 1
            temp_file = RemoveDuplicatesView._save_to_temp(df_filled, dataset.file_type)
            
            new_version = DatasetVersion.objects.create(
                dataset=dataset,
                version_number=new_version_num,
                operation_type='fill_empty',
                operation_description=f"Filled {result['total_cells_filled']} empty cells",
                rows_before=len(df),
                rows_after=len(df_filled),
                changes_made=result,
            )
            
            with open(temp_file, 'rb') as f:
                new_version.file.save(
                    f"{dataset.name}_v{new_version_num}.csv",
                    ContentFile(f.read())
                )
            
            CleaningOperation.objects.create(
                dataset=dataset,
                operation_type='fill_empty',
                parameters=cells_to_fill,
                created_by_version=new_version,
                result=result,
                status='success',
            )
            
            version.is_current = False
            version.save()
            new_version.is_current = True
            new_version.save()
            
            create_notification(
                user=request.user,
                title='Empty Cells Filled',
                message=f"Filled {result['total_cells_filled']} empty cells. New version created.",
                notification_type='success',
                related_app='datasets',
                related_model='Dataset',
                related_object_id=dataset.id
            )
            
            return JsonResponse({
                'status': 'success',
                'cells_filled': result['total_cells_filled'],
                'new_version_id': new_version.id,
            })
        
        except Exception as e:
            logger.error(f"Error filling empty cells: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


# ============================================================================
# VISUALIZATIONS
# ============================================================================

class VisualizationCreateView(LoginRequiredMixin, OwnerCheckMixin, View):
    """Create new visualization from dataset"""
    
    def get(self, request, pk):
        """Display visualization creation form"""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        # Get sample data
        try:
            df = FileParser.parse_file(dataset.file.path, dataset.file_type)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            string_cols = df.select_dtypes(include=['object']).columns.tolist()
        except Exception as e:
            numeric_cols = []
            string_cols = []
        
        context = {
            'dataset': dataset,
            'visualization_types': Visualization.CHART_TYPES,
            'numeric_columns': numeric_cols,
            'string_columns': string_cols,
            'all_columns': list(df.columns) if 'df' in locals() else [],
        }
        
        return render(request, 'datasets/visualization/create.html', context)
    
    def post(self, request, pk):
        """Create visualization"""
        dataset = get_object_or_404(Dataset, pk=pk)
        self.check_owner(dataset, request.user)
        
        try:
            data = json.loads(request.body)
            chart_type = data.get('chart_type')
            title = data.get('title', f'{chart_type.title()} Chart')
            x_column = data.get('x_column')
            y_columns = data.get('y_columns', [])
            
            # Validate inputs
            if not chart_type:
                return JsonResponse({'error': 'chart_type is required'}, status=400)
            
            if not x_column:
                return JsonResponse({'error': 'x_column is required'}, status=400)
            
            # Parse file
            df = FileParser.parse_file(dataset.file.path, dataset.file_type)
            
            # Validate columns exist
            if x_column not in df.columns:
                return JsonResponse({'error': f'Column {x_column} not found in dataset'}, status=400)
            
            # Validate y columns if provided
            if y_columns:
                for col in y_columns:
                    if col not in df.columns:
                        return JsonResponse({'error': f'Column {col} not found in dataset'}, status=400)
            
            # Create visualization
            engine = VisualizationEngine(df)
            
            # Build kwargs based on chart type
            viz_kwargs = {
                'title': title,
                'x_column': x_column,
            }
            
            # Add y_columns for types that need it
            if chart_type in ['line', 'bar', 'scatter', 'area']:
                if y_columns:
                    viz_kwargs['y_columns'] = y_columns
                else:
                    # Use numeric columns as defaults
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        viz_kwargs['y_columns'] = numeric_cols[:3]  # Limit to 3 columns
            elif chart_type in ['histogram', 'pie', 'distribution']:
                # These only need the x column
                viz_kwargs['column'] = x_column
                viz_kwargs.pop('x_column', None)
            elif chart_type == 'heatmap':
                # Heatmap uses numeric columns
                viz_kwargs.pop('x_column', None)
                viz_kwargs['columns'] = df.select_dtypes(include=['number']).columns.tolist()
            elif chart_type == 'boxplot':
                viz_kwargs.pop('x_column', None)
                viz_kwargs['columns'] = df.select_dtypes(include=['number']).columns.tolist()
            
            # Remove None values
            viz_kwargs = {k: v for k, v in viz_kwargs.items() if v is not None}
            
            fig = engine.create_visualization(chart_type, **viz_kwargs)
            chart_html = engine.to_html(fig)
            
            # Save visualization
            visualization = Visualization.objects.create(
                dataset=dataset,
                name=title,
                chart_type=chart_type,
                x_column=x_column,
                y_columns=y_columns if y_columns else [],
                config={
                    'x_column': x_column,
                    'y_columns': y_columns if y_columns else [],
                },
                chart_html=chart_html,
                is_published=True,
            )
            
            create_notification(
                user=request.user,
                title='Visualization Created',
                message=f"New {chart_type} visualization '{title}' created.",
                notification_type='success',
                related_app='datasets',
                related_model='Visualization',
                related_object_id=visualization.id
            )
            
            return JsonResponse({
                'status': 'success',
                'visualization_id': visualization.id,
                'redirect_url': reverse_lazy('datasets:visualization_detail', kwargs={'pk': visualization.id})
            })
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=400)


class VisualizationDetailView(LoginRequiredMixin, OwnerCheckMixin, DetailView):
    """Display visualization"""
    model = Visualization
    template_name = 'datasets/visualization/detail.html'
    context_object_name = 'visualization'
    
    def get_object(self):
        """Get visualization and verify ownership"""
        obj = super().get_object()
        self.check_owner(obj.dataset, self.request.user)
        return obj


# ============================================================================
# ANALYTICS AND DASHBOARD
# ============================================================================

class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """
    User Analytics Dashboard showing:
    - Total files uploaded/processed
    - Most used operations
    - Recent activity
    - Data quality insights
    """
    template_name = 'datasets/analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Build analytics context"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Dataset statistics
        datasets = Dataset.objects.filter(owner=user)
        context['total_datasets'] = datasets.count()
        context['analyzed_datasets'] = datasets.filter(is_analyzed=True).count()
        context['cleaned_datasets'] = datasets.filter(is_cleaned=True).count()
        
        # Operations statistics
        operations = CleaningOperation.objects.filter(dataset__owner=user)
        context['total_operations'] = operations.count()
        context['successful_operations'] = operations.filter(status='success').count()
        
        # Operation types breakdown
        operation_breakdown = {}
        for op_type in dict(OPERATION_TYPE_CHOICES).keys():
            count = operations.filter(operation_type=op_type, status='success').count()
            if count > 0:
                operation_breakdown[op_type] = count
        context['operation_breakdown'] = operation_breakdown
        
        # Visualizations
        visualizations = Visualization.objects.filter(dataset__owner=user)
        context['total_visualizations'] = visualizations.count()
        
        # Visualization types breakdown
        viz_breakdown = {}
        for viz_type, viz_label in Visualization.CHART_TYPES:
            count = visualizations.filter(chart_type=viz_type).count()
            if count > 0:
                viz_breakdown[viz_type] = count
        context['visualization_breakdown'] = viz_breakdown
        
        # Data quality statistics
        avg_quality = datasets.filter(data_quality_score__gt=0).aggregate(
            avg=Avg('data_quality_score')
        )['avg'] or 0
        context['avg_data_quality'] = round(avg_quality, 2)
        
        # Recent activity
        recent_datasets = datasets.order_by('-uploaded_at')[:5]
        context['recent_datasets'] = recent_datasets
        
        recent_operations = operations.filter(status='success').order_by('-created_at')[:5]
        context['recent_operations'] = recent_operations
        
        recent_visualizations = visualizations.order_by('-created_at')[:5]
        context['recent_visualizations'] = recent_visualizations
        
        # File type distribution
        file_types = datasets.values('file_type').annotate(count=Count('id'))
        context['file_types'] = {item['file_type']: item['count'] for item in file_types}
        
        return context


# ============================================================================
# REST API VIEWSETS
# ============================================================================

class DatasetViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Dataset model.
    Provides comprehensive CRUD operations and dataset management.
    """
    serializer_class = DatasetSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    ordering_fields = ['uploaded_at', 'name', 'data_quality_score']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter datasets to user's datasets"""
        return Dataset.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set owner to current user and analyze"""
        dataset = serializer.save(owner=self.request.user)
        
        # Auto-analyze
        try:
            file_type = FileParser.detect_file_type(dataset.file.name)
            dataset.file_type = file_type
            dataset.file_size = dataset.file.size
            dataset.save()
            
            # Analyze
            df = FileParser.parse_file(dataset.file.path, file_type)
            analyzer = FileAnalyzer(df)
            analysis = analyzer.analyze()
            
            dataset.row_count = len(df)
            dataset.col_count = len(df.columns)
            dataset.column_names = list(df.columns)
            dataset.is_analyzed = True
            dataset.data_quality_score = analysis['data_quality_score']
            dataset.summary = analysis['summary']
            dataset.save()
            
            FileAnalysis.objects.create(dataset=dataset, analysis_data=analysis)
        except Exception as e:
            logger.error(f"Error in auto-analysis: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        """Get detailed analysis for dataset"""
        dataset = self.get_object()
        try:
            analysis = FileAnalysis.objects.get(dataset=dataset)
            return Response(analysis.analysis_data)
        except FileAnalysis.DoesNotExist:
            return Response({'error': 'Analysis not available'}, status=404)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of dataset"""
        dataset = self.get_object()
        versions = dataset.versions.all().values(
            'id', 'version_number', 'operation_type', 'created_at',
            'operation_description', 'rows_before', 'rows_after'
        )
        return Response(list(versions))
    
    @action(detail=True, methods=['post'])
    def deduplicate(self, request, pk=None):
        """Remove duplicates and create new version"""
        dataset = self.get_object()
        # Delegate to view
        view = RemoveDuplicatesView()
        return view.post(request, pk)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics about user's datasets"""
        datasets = self.get_queryset()
        return Response({
            'total_datasets': datasets.count(),
            'analyzed_datasets': datasets.filter(is_analyzed=True).count(),
            'cleaned_datasets': datasets.filter(is_cleaned=True).count(),
            'avg_quality_score': datasets.filter(data_quality_score__gt=0).aggregate(
                avg=Avg('data_quality_score')
            )['avg'] or 0,
            'total_visualizations': Visualization.objects.filter(
                dataset__owner=request.user
            ).count(),
        })
