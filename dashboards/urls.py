"""
URL routing for dashboards app.
"""

from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    # Dashboard CRUD
    path('', views.DashboardListView.as_view(), name='dashboard_list'),
    path('create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('<int:pk>/edit/', views.DashboardUpdateView.as_view(), name='dashboard_edit'),
    path('<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),
    
    # Dashboard actions
    path('<int:pk>/publish/', views.DashboardPublishView.as_view(), name='dashboard_publish'),
    path('<int:pk>/layout/', views.DashboardLayoutView.as_view(), name='dashboard_layout'),
    path('<int:pk>/visualizations/', views.DashboardVisualizationView.as_view(), name='dashboard_visualizations'),
]
