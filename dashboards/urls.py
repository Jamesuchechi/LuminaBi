"""
Enhanced URL routing for dashboards app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dashboards'

# REST API Router
router = DefaultRouter()
router.register(r'api/dashboards', views.DashboardViewSet, basename='dashboard-api')
router.register(r'api/widgets', views.DashboardWidgetViewSet, basename='widget-api')
router.register(r'api/insights', views.DashboardInsightViewSet, basename='insight-api')
router.register(r'api/interpretability', views.InterpretabilityAnalysisViewSet, basename='interpretability-api')

urlpatterns = [
    
    # Dashboard CRUD
    path('', views.DashboardListView.as_view(), name='dashboard_list'),
    path('dashboards/create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('dashboards/<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('dashboards/<int:pk>/edit/', views.DashboardUpdateView.as_view(), name='dashboard_edit'),
    path('dashboards/<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),
    
    # Dashboard Actions
    path('dashboards/<int:pk>/publish/', views.DashboardPublishView.as_view(), name='dashboard_publish'),
    path('dashboards/<int:pk>/layout/', views.DashboardLayoutView.as_view(), name='dashboard_layout'),
    path('dashboards/<int:pk>/visualizations/', views.DashboardVisualizationView.as_view(), name='dashboard_visualizations'),
    path('dashboards/<int:pk>/refresh-insights/', views.DashboardRefreshInsightsView.as_view(), name='dashboard_refresh_insights'),
    
    # Dashboard Insights
    path('dashboards/<int:pk>/insights/', views.DashboardInsightsView.as_view(), name='dashboard_insights'),
    path('insights/<int:pk>/acknowledge/', views.InsightAcknowledgeView.as_view(), name='insight_acknowledge'),
    
    # Interpretability
    path('dashboards/<int:pk>/interpretability/', views.InterpretabilityAnalysisView.as_view(), name='interpretability_list'),
    path('interpretability/<int:pk>/', views.InterpretabilityDetailView.as_view(), name='interpretability_detail'),
    
    # REST API
    path('', include(router.urls)),
]