"""
WebSocket consumers for real-time updates.
Handles WebSocket connections for data cleaning, insights, dashboards, and file uploads.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class BaseConsumer(AsyncWebsocketConsumer):
    """Base WebSocket consumer with common functionality."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        
        await self.accept()
        logger.info(f'User {self.user.id} connected to {self.__class__.__name__}')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f'User {self.user.id} disconnected from {self.__class__.__name__}')
    
    async def send_json(self, content):
        """Send JSON data to client."""
        await self.send(text_data=json.dumps(content))
    
    async def receive_json(self, content):
        """Receive JSON data from client."""
        logger.debug(f'Received JSON: {content}')


class DataCleaningConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time data cleaning progress updates.
    Sends cleaning status, progress percentage, and error notifications.
    """
    
    async def connect(self):
        self.dataset_id = self.scope['url_route']['kwargs']['dataset_id']
        self.group_name = f'datacleaning_{self.dataset_id}'
        
        # Add to group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await super().connect()
    
    async def disconnect(self, close_code):
        # Remove from group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await super().disconnect(close_code)
    
    async def cleaning_progress(self, event):
        """Handle cleaning progress updates."""
        await self.send_json({
            'type': 'cleaning_progress',
            'progress': event['progress'],
            'status': event['status'],
            'current_step': event.get('current_step', ''),
        })
    
    async def cleaning_complete(self, event):
        """Handle cleaning completion."""
        await self.send_json({
            'type': 'cleaning_complete',
            'dataset_id': self.dataset_id,
            'status': 'success',
        })
    
    async def cleaning_error(self, event):
        """Handle cleaning errors."""
        await self.send_json({
            'type': 'cleaning_error',
            'error': event['error'],
            'details': event.get('details', ''),
        })


class InsightsConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time insights generation updates.
    Sends insights, correlations, trends, and anomalies as they are discovered.
    """
    
    async def connect(self):
        self.dataset_id = self.scope['url_route']['kwargs']['dataset_id']
        self.group_name = f'insights_{self.dataset_id}'
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await super().connect()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await super().disconnect(close_code)
    
    async def insight_discovered(self, event):
        """Handle discovered insights."""
        await self.send_json({
            'type': 'insight_discovered',
            'insight_type': event['insight_type'],  # trend, correlation, anomaly, etc.
            'data': event['data'],
        })
    
    async def insights_complete(self, event):
        """Handle insights generation completion."""
        await self.send_json({
            'type': 'insights_complete',
            'dataset_id': self.dataset_id,
            'total_insights': event.get('total_insights', 0),
        })


class DashboardConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    Handles dashboard changes, filter updates, and collaborative edits.
    """
    
    async def connect(self):
        self.dashboard_id = self.scope['url_route']['kwargs']['dashboard_id']
        self.group_name = f'dashboard_{self.dashboard_id}'
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await super().connect()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await super().disconnect(close_code)
    
    async def receive_json(self, content):
        """Handle incoming dashboard updates."""
        action = content.get('action')
        
        if action == 'update_filter':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'dashboard_filter_update',
                    'filter': content.get('filter'),
                    'user_id': self.user.id,
                }
            )
    
    async def dashboard_update(self, event):
        """Handle dashboard updates."""
        await self.send_json({
            'type': 'dashboard_update',
            'data': event['data'],
        })
    
    async def dashboard_filter_update(self, event):
        """Handle filter updates."""
        if event['user_id'] != self.user.id:  # Don't send back to sender
            await self.send_json({
                'type': 'filter_update',
                'filter': event['filter'],
                'updated_by': event['user_id'],
            })


class UploadProgressConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time file upload progress.
    Sends upload progress percentage and status updates.
    """
    
    async def connect(self):
        self.upload_id = self.scope['url_route']['kwargs']['upload_id']
        self.group_name = f'upload_{self.upload_id}'
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await super().connect()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await super().disconnect(close_code)
    
    async def upload_progress(self, event):
        """Handle upload progress updates."""
        await self.send_json({
            'type': 'upload_progress',
            'progress': event['progress'],
            'uploaded_bytes': event['uploaded_bytes'],
            'total_bytes': event['total_bytes'],
        })
    
    async def upload_complete(self, event):
        """Handle upload completion."""
        await self.send_json({
            'type': 'upload_complete',
            'upload_id': self.upload_id,
            'file_id': event.get('file_id'),
            'status': 'success',
        })
    
    async def upload_error(self, event):
        """Handle upload errors."""
        await self.send_json({
            'type': 'upload_error',
            'error': event['error'],
        })
