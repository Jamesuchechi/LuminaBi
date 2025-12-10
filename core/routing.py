"""
WebSocket URL routing for real-time features.
Maps WebSocket endpoints to their corresponding consumers.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Data cleaning progress updates
    path('ws/data-cleaning/<int:dataset_id>/', consumers.DataCleaningConsumer.as_asgi()),
    
    # Insights generation real-time updates
    path('ws/insights/<int:dataset_id>/', consumers.InsightsConsumer.as_asgi()),
    
    # Dashboard updates and notifications
    path('ws/dashboard/<int:dashboard_id>/', consumers.DashboardConsumer.as_asgi()),
    path('ws/dashboard-hub/', consumers.DashboardHubConsumer.as_asgi()),
    
    # File upload progress
    path('ws/upload-progress/<int:upload_id>/', consumers.UploadProgressConsumer.as_asgi()),
]
