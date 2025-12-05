"""
URL configuration for the core application.
Handles organizational, settings, and audit management.
"""

from django.urls import path
from . import views

app_name = 'core'

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
]
