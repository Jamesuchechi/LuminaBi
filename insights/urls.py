"""
URL routing for insights app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'insights'

# REST API Router
router = DefaultRouter()
router.register(r'api/insights', views.InsightViewSet, basename='insight-api')
router.register(r'api/anomalies', views.AnomalyViewSet, basename='anomaly-api')
router.register(r'api/outliers', views.OutlierViewSet, basename='outlier-api')

urlpatterns = [
    # Insight views
    path('', views.InsightListView.as_view(), name='insight_list'),
    path('insights/<int:pk>/', views.InsightDetailView.as_view(), name='insight_detail'),
    
    # Run insights on dataset
    path('run/', views.RunInsightsAPIView.as_view(), name='run_insights'),
    
    # Dataset insights
    path('datasets/<int:dataset_id>/insights/', views.DatasetInsightsView.as_view(), name='dataset_insights'),
    path('datasets/<int:dataset_id>/generate-insights/', views.GenerateInsightsView.as_view(), name='generate_insights'),
    
    # Anomalies
    path('anomalies/', views.AnomalyListView.as_view(), name='anomaly_list'),
    path('anomalies/<int:pk>/', views.AnomalyDetailView.as_view(), name='anomaly_detail'),
    
    # Outliers
    path('outliers/', views.OutlierListView.as_view(), name='outlier_list'),
    path('outliers/<int:pk>/', views.OutlierDetailView.as_view(), name='outlier_detail'),
    
    # Relationships
    path('relationships/', views.RelationshipListView.as_view(), name='relationship_list'),
    path('relationships/<int:pk>/', views.RelationshipDetailView.as_view(), name='relationship_detail'),
    
    # REST API
    path('', include(router.urls)),
]
