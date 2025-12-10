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
    
    # Comments
    path('<int:pk>/comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('<int:pk>/comments/<int:comment_id>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    
    # Tags
    path('<int:pk>/tags/add/', views.TagAddView.as_view(), name='tag_add'),
    path('<int:pk>/tags/<int:tag_id>/remove/', views.TagRemoveView.as_view(), name='tag_remove'),
    
    # Favorites
    path('<int:pk>/favorite/', views.FavoriteToggleView.as_view(), name='favorite_toggle'),
]
