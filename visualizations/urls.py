"""
URL routing for visualizations application.
Handles visualization management, display, and configuration.
"""

from django.urls import path
from . import views

app_name = 'visualizations'

urlpatterns = [
    # Visualization list and management
    path('', views.VisualizationListView.as_view(), name='visualization_list'),
    path('create/', views.VisualizationCreateView.as_view(), name='visualization_create'),
    path('<int:pk>/', views.VisualizationDetailView.as_view(), name='visualization_detail'),
    path('<int:pk>/edit/', views.VisualizationUpdateView.as_view(), name='visualization_edit'),
    path('<int:pk>/delete/', views.VisualizationDeleteView.as_view(), name='visualization_delete'),
    
    # Visualization operations
    path('<int:pk>/publish/', views.VisualizationPublishView.as_view(), name='visualization_publish'),
    path('<int:pk>/preview/', views.VisualizationPreviewView.as_view(), name='visualization_preview'),
]
