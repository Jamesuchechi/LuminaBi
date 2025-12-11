"""
URL routing for API application.
REST API endpoints for all resources.
"""

from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import (
    OrganizationViewSet, SettingViewSet, AuditLogViewSet,
    InsightViewSet, ReportViewSet, TrendViewSet, AnomalyViewSet,
    AlertViewSet, MetricViewSet, AnalyticsDashboardViewSet,
    DatasetViewSet, VisualizationViewSet, DashboardModelViewSet
)
from visualizations import views as viz_views

app_name = 'api'

# DRF Router for automatic CRUD routes
router = routers.DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'settings', SettingViewSet, basename='setting')
router.register(r'audit-logs', AuditLogViewSet, basename='audit_log')
router.register(r'insights', InsightViewSet, basename='insight')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'trends', TrendViewSet, basename='trend')
router.register(r'anomalies', AnomalyViewSet, basename='anomaly')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'metrics', MetricViewSet, basename='metric')
router.register(r'analytics-dashboards', AnalyticsDashboardViewSet, basename='analytics_dashboard')
router.register(r'datasets', DatasetViewSet, basename='dataset')
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'dashboard-models', DashboardModelViewSet, basename='dashboard_model')

urlpatterns = [
    # Direct preview-config endpoint (MUST come before router.urls to be matched first)
    path('visualizations/preview-config/', viz_views.preview_config_direct, name='visualization_preview_config'),

    # API Routes (router)
    path('', include(router.urls)),

    # Health check
    path('health/', views.health_check, name='health'),

    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
