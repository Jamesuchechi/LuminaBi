"""
URL routing for analytics app.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Analytics dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    
    # Insights
    path('insights/', views.InsightListView.as_view(), name='insight_list'),
    path('insights/<int:pk>/', views.InsightDetailView.as_view(), name='insight_detail'),
    path('insights/<int:pk>/validate/', views.InsightValidateView.as_view(), name='insight_validate'),
    
    # Reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/publish/', views.ReportPublishView.as_view(), name='report_publish'),
    
    # Anomalies
    path('anomalies/', views.AnomalyListView.as_view(), name='anomaly_list'),
    path('anomalies/<int:pk>/', views.AnomalyDetailView.as_view(), name='anomaly_detail'),
    path('anomalies/<int:pk>/acknowledge/', views.AnomalyAcknowledgeView.as_view(), name='anomaly_acknowledge'),
    path('anomalies/<int:pk>/resolve/', views.AnomalyResolveView.as_view(), name='anomaly_resolve'),
    
    # Alerts
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/acknowledge/', views.AlertAcknowledgeView.as_view(), name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views.AlertResolveView.as_view(), name='alert_resolve'),
    
    # Metrics
    path('metrics/', views.MetricListView.as_view(), name='metric_list'),
    path('metrics/<int:pk>/', views.MetricDetailView.as_view(), name='metric_detail'),
    
    # Dashboards
    path('dashboards/', views.DashboardListView.as_view(), name='dashboard_list'),
    path('dashboards/<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('dashboards/create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('dashboards/<int:pk>/edit/', views.DashboardUpdateView.as_view(), name='dashboard_edit'),
    path('dashboards/<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),
]
