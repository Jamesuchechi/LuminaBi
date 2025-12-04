"""
URL routing for datasets application.
Handles dataset management, upload, and visualization URLs.
"""

from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    # Dataset list and management
    path('', views.DatasetListView.as_view(), name='dataset_list'),
    path('create/', views.DatasetCreateView.as_view(), name='dataset_create'),
    path('<int:pk>/', views.DatasetDetailView.as_view(), name='dataset_detail'),
    path('<int:pk>/edit/', views.DatasetUpdateView.as_view(), name='dataset_edit'),
    path('<int:pk>/delete/', views.DatasetDeleteView.as_view(), name='dataset_delete'),
    
    # Dataset operations
    path('<int:pk>/clean/', views.DatasetCleaningView.as_view(), name='dataset_clean'),
    path('<int:pk>/preview/', views.DatasetPreviewView.as_view(), name='dataset_preview'),
    path('<int:pk>/export/', views.DatasetExportView.as_view(), name='dataset_export'),
]
