"""
URL configuration for the core application.
Handles organizational, settings, audit management, and dashboards.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

# REST API Router for dashboard endpoints
router = DefaultRouter()
router.register(r'api/dashboards', views.DashboardViewSet, basename='dashboard-api')
router.register(r'api/widgets', views.DashboardWidgetViewSet, basename='widget-api')
router.register(r'api/insights', views.DashboardInsightViewSet, basename='insight-api')
router.register(r'api/interpretability', views.InterpretabilityAnalysisViewSet, basename='interpretability-api')

urlpatterns = [
    # ====================================================================
    # ORGANIZATION MANAGEMENT
    # ====================================================================
    path('dashboard/', views.IndexView.as_view(), name='index'),
    path('organizations/', views.OrganizationListView.as_view(), name='organization_list'),
    path('organizations/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization_detail'),
    path('organizations/<int:pk>/edit/', views.OrganizationUpdateView.as_view(), name='organization_update'),
    path('organizations/<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='organization_delete'),
    
    # ====================================================================
    # ORGANIZATION API (JSON)
    # ====================================================================
    path('api/organizations/<int:pk>/', views.OrganizationAPIView.as_view(), name='api_organization'),
    
    # ====================================================================
    # SETTINGS MANAGEMENT (Admin only)
    # ====================================================================
    path('user-settings/', views.UserSettingsView.as_view(), name='user_settings'),
    path('settings/', views.SettingsListView.as_view(), name='settings_list'),
    path('settings/<int:pk>/edit/', views.SettingsUpdateView.as_view(), name='settings_update'),
    
    # ====================================================================
    # SETTINGS API (JSON)
    # ====================================================================
    path('api/settings/<str:key>/', views.SettingAPIView.as_view(), name='api_setting'),
    
    # ====================================================================
    # AUDIT LOG VIEWS (Admin only)
    # ====================================================================
    path('audit/', views.AuditLogListView.as_view(), name='audit_logs'),
    
    # ====================================================================
    # SYSTEM MANAGEMENT
    # ====================================================================
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('stats/', views.SystemStatsView.as_view(), name='system_stats'),
    
    # ====================================================================
    # NOTIFICATIONS VIEWS & API
    # ====================================================================
    path('notifications/', views.NotificationsPageView.as_view(), name='notifications'),
    path('api/notifications/unread/', views.UnreadNotificationsAPIView.as_view(), name='api_unread_notifications'),
    path('api/notifications/', views.NotificationsListAPIView.as_view(), name='api_notifications'),
    path('api/notifications/<int:pk>/read/', views.NotificationMarkReadAPIView.as_view(), name='api_notification_read'),
    
    # ====================================================================
    # DASHBOARD CRUD (migrated from dashboards app)
    # ====================================================================
    path('dashboards/', views.DashboardListView.as_view(), name='dashboard_list'),
    path('dashboards/create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('dashboards/<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('dashboards/<int:pk>/edit/', views.DashboardUpdateView.as_view(), name='dashboard_edit'),
    path('dashboards/<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),
    
    # ====================================================================
    # DASHBOARD ACTIONS
    # ====================================================================
    path('dashboards/<int:pk>/publish/', views.DashboardPublishView.as_view(), name='dashboard_publish'),
    path('dashboards/<int:pk>/layout/', views.DashboardLayoutView.as_view(), name='dashboard_layout'),
    path('dashboards/<int:pk>/visualizations/', views.DashboardVisualizationView.as_view(), name='dashboard_visualizations'),
    path('dashboards/<int:pk>/refresh-insights/', views.DashboardRefreshInsightsView.as_view(), name='dashboard_refresh_insights'),
    
    # ====================================================================
    # DASHBOARD INSIGHTS
    # ====================================================================
    path('dashboards/<int:pk>/insights/', views.DashboardInsightsView.as_view(), name='dashboard_insights'),
    path('insights/<int:pk>/acknowledge/', views.InsightAcknowledgeView.as_view(), name='insight_acknowledge'),
    
    # ====================================================================
    # INTERPRETABILITY ANALYSIS
    # ====================================================================
    path('dashboards/<int:pk>/interpretability/', views.InterpretabilityAnalysisView.as_view(), name='interpretability_list'),
    path('interpretability/<int:pk>/', views.InterpretabilityDetailView.as_view(), name='interpretability_detail'),
    
    # ====================================================================
    # REST API (Dashboard endpoints)
    # ====================================================================
    path('', include(router.urls)),
]
