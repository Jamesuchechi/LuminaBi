"""
WebSocket URL routing for insights app
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/insights/(?P<dataset_id>\w+)/$', consumers.InsightGenerationConsumer.as_asgi()),
    re_path(r'ws/insights/detail/(?P<insight_id>\w+)/$', consumers.InsightDetailConsumer.as_asgi()),
]
