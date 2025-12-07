"""
URL routing for datasets application with complete file intelligence system.
Handles file upload, analysis, cleaning, visualization, and analytics.
"""

from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    # ===== Dataset Management =====
    path('', views.DatasetListView.as_view(), name='dataset_list'),
    path('upload/', views.DatasetUploadView.as_view(), name='dataset_upload'),
    path('<int:pk>/', views.DatasetDetailView.as_view(), name='dataset_detail'),
    path('<int:pk>/analysis/', views.DatasetAnalysisView.as_view(), name='dataset_analysis'),
    
    # ===== File Viewer =====
    path('<int:pk>/viewer/', views.FileViewerView.as_view(), name='file_viewer'),
    
    # ===== Data Cleaning Operations =====
    path('<int:pk>/remove-duplicates/', views.RemoveDuplicatesView.as_view(), name='remove_duplicates'),
    path('<int:pk>/fill-empty-cells/', views.FillEmptyCellsView.as_view(), name='fill_empty_cells'),
    
    # ===== Visualizations =====
    path('<int:pk>/visualizations/create/', views.VisualizationCreateView.as_view(), name='visualization_create'),
    path('visualization/<int:pk>/', views.VisualizationDetailView.as_view(), name='visualization_detail'),
    
    # ===== Analytics =====
    path('analytics/dashboard/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
]
