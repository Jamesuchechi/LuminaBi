"""
WebSocket consumers for real-time insights generation
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from datasets.models import Dataset
from .models import DataInsight, AnomalyDetection, OutlierAnalysis, RelationshipAnalysis
from .services import InsightGenerator
import pandas as pd
import traceback

logger = logging.getLogger(__name__)


class InsightGenerationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time insight generation
    Streams generation progress and results to frontend
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.dataset_id = self.scope['url_route']['kwargs']['dataset_id']
        self.user = self.scope['user']
        self.room_group_name = f'insights_{self.dataset_id}'

        # Check user authentication
        if not self.user.is_authenticated:
            await self.close()
            return

        # Add to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_json({
            'status': 'connected',
            'message': 'Connected to insight generation service'
        })

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'generate':
                await self.handle_generate_insights()
            elif action == 'cancel':
                await self.send_json({
                    'status': 'cancelled',
                    'message': 'Insight generation cancelled'
                })
            else:
                await self.send_json({
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                })
        except json.JSONDecodeError:
            await self.send_json({
                'status': 'error',
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await self.send_json({
                'status': 'error',
                'message': str(e)
            })

    async def handle_generate_insights(self):
        """Generate insights for the dataset"""
        try:
            # Verify dataset ownership
            dataset = await self.get_dataset()
            if not dataset:
                await self.send_json({
                    'status': 'error',
                    'message': 'Dataset not found'
                })
                return

            # Send initialization message
            await self.send_json({
                'status': 'initializing',
                'progress': 0,
                'message': 'Loading dataset...'
            })

            # Load dataset
            df = await self.load_dataset_dataframe(dataset)
            if df is None or df.empty:
                await self.send_json({
                    'status': 'error',
                    'message': 'Failed to load dataset or dataset is empty'
                })
                return

            # Update progress
            await self.send_json({
                'status': 'processing',
                'progress': 10,
                'message': 'Initializing analysis engine...'
            })

            # Generate insights
            generator = InsightGenerator(df, self.dataset_id)

            # Generate summary statistics
            await self.send_json({
                'status': 'processing',
                'progress': 20,
                'message': 'Generating summary statistics...'
            })
            summary = generator.generate_summary_statistics()

            # Detect anomalies
            await self.send_json({
                'status': 'processing',
                'progress': 40,
                'message': 'Detecting anomalies...'
            })
            anomalies = generator.detect_anomalies()

            # Detect outliers
            await self.send_json({
                'status': 'processing',
                'progress': 60,
                'message': 'Analyzing outliers...'
            })
            outliers = generator.detect_outliers()

            # Analyze relationships
            await self.send_json({
                'status': 'processing',
                'progress': 75,
                'message': 'Analyzing feature relationships...'
            })
            relationships = generator.analyze_relationships()

            # Analyze distributions
            await self.send_json({
                'status': 'processing',
                'progress': 85,
                'message': 'Analyzing distributions...'
            })
            distributions = generator.analyze_distributions()

            # Analyze missing data
            await self.send_json({
                'status': 'processing',
                'progress': 90,
                'message': 'Analyzing data quality...'
            })
            missing_data = generator.analyze_missing_data()

            # Save to database
            await self.send_json({
                'status': 'processing',
                'progress': 95,
                'message': 'Saving results to database...'
            })

            insight_count = await self.save_insights(
                dataset,
                summary,
                anomalies,
                outliers,
                relationships,
                distributions,
                missing_data
            )

            # Completion
            await self.send_json({
                'status': 'completed',
                'progress': 100,
                'message': f'Successfully generated {insight_count} insights',
                'results': {
                    'insights': insight_count,
                    'anomalies': len(anomalies),
                    'outliers': len(outliers),
                    'relationships': len(relationships),
                }
            })

        except Exception as e:
            logger.error(f"Insight generation error: {str(e)}\n{traceback.format_exc()}")
            await self.send_json({
                'status': 'error',
                'message': f'Error generating insights: {str(e)}'
            })

    # Database operations
    @database_sync_to_async
    def get_dataset(self):
        """Get dataset and verify ownership"""
        try:
            return Dataset.objects.get(id=self.dataset_id, user=self.user)
        except Dataset.DoesNotExist:
            return None

    @database_sync_to_async
    def load_dataset_dataframe(self, dataset):
        """Load dataset file as pandas DataFrame"""
        try:
            if dataset.file:
                if dataset.file.name.endswith('.csv'):
                    return pd.read_csv(dataset.file.path)
                elif dataset.file.name.endswith('.xlsx'):
                    return pd.read_excel(dataset.file.path)
                elif dataset.file.name.endswith('.json'):
                    return pd.read_json(dataset.file.path)
            return None
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            return None

    @database_sync_to_async
    def save_insights(self, dataset, summary, anomalies, outliers, relationships, distributions, missing_data):
        """Save generated insights to database"""
        try:
            insight_count = 0

            # Save main insight with summary
            insight, _ = DataInsight.objects.update_or_create(
                dataset=dataset,
                defaults={
                    'title': f'Analysis Report - {dataset.name}',
                    'description': f'Comprehensive analysis of {dataset.name}',
                    'insight_type': 'summary',
                    'analysis_data': {
                        'summary': summary,
                        'distributions': distributions,
                        'missing_data': missing_data,
                    },
                    'confidence_score': 95.0,
                }
            )
            insight_count += 1

            # Save anomaly detections
            for col, anomaly_data in anomalies.items():
                if anomaly_data:
                    for method, values in anomaly_data.items():
                        if values and 'count' in values:
                            AnomalyDetection.objects.create(
                                dataset=dataset,
                                affected_columns=[col],
                                anomaly_type=method,
                                affected_rows=values.get('indices', []),
                                severity=self._classify_severity(
                                    len(values.get('indices', [])) / len(dataset.row_count) if dataset.row_count else 0
                                ),
                                analysis_data=values,
                            )
                            insight_count += 1

            # Save outlier analyses
            for col, outlier_data in outliers.items():
                if outlier_data:
                    for method, indices in outlier_data.items():
                        if indices:
                            OutlierAnalysis.objects.create(
                                dataset=dataset,
                                column=col,
                                method=method,
                                outlier_indices=indices,
                                outlier_count=len(indices),
                                outlier_percentage=(len(indices) / len(dataset.row_count) * 100) if dataset.row_count else 0,
                                analysis_data={'method': method, 'indices': indices},
                            )
                            insight_count += 1

            # Save relationships
            for rel in relationships:
                RelationshipAnalysis.objects.create(
                    dataset=dataset,
                    feature_1=rel['feature_1'],
                    feature_2=rel['feature_2'],
                    correlation_coefficient=rel['correlation'],
                    p_value=rel.get('p_value', 0),
                    relationship_type=rel.get('relationship_type', 'correlation'),
                    description=rel.get('description', ''),
                    analysis_data=rel,
                )
                insight_count += 1

            return insight_count

        except Exception as e:
            logger.error(f"Error saving insights: {str(e)}")
            raise

    @staticmethod
    def _classify_severity(ratio: float) -> str:
        """Classify anomaly severity based on ratio"""
        if ratio > 0.1:
            return 'critical'
        elif ratio > 0.05:
            return 'high'
        elif ratio > 0.02:
            return 'medium'
        else:
            return 'low'


class InsightDetailConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming detailed insight explanations
    Uses SHAP/LIME for feature importance visualization
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.insight_id = self.scope['url_route']['kwargs']['insight_id']
        self.user = self.scope['user']
        self.room_group_name = f'insight_detail_{self.insight_id}'

        # Check user authentication
        if not self.user.is_authenticated:
            await self.close()
            return

        # Add to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'load_shap_data':
                await self.handle_load_shap_data()
            elif action == 'load_lime_data':
                await self.handle_load_lime_data(data.get('instance_idx'))
            else:
                await self.send_json({
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                })
        except Exception as e:
            logger.error(f"DetailConsumer error: {str(e)}")
            await self.send_json({
                'status': 'error',
                'message': str(e)
            })

    async def handle_load_shap_data(self):
        """Load SHAP explanation data"""
        try:
            insight = await self.get_insight()
            if not insight:
                await self.send_json({
                    'status': 'error',
                    'message': 'Insight not found'
                })
                return

            # Get SHAP data from insight model if available
            shap_data = await self.calculate_shap_values(insight)

            await self.send_json({
                'status': 'success',
                'type': 'shap_data',
                'data': shap_data
            })

        except Exception as e:
            logger.error(f"Error loading SHAP data: {str(e)}")
            await self.send_json({
                'status': 'error',
                'message': str(e)
            })

    async def handle_load_lime_data(self, instance_idx):
        """Load LIME explanation data"""
        try:
            insight = await self.get_insight()
            if not insight:
                await self.send_json({
                    'status': 'error',
                    'message': 'Insight not found'
                })
                return

            # Get LIME data from insight model if available
            lime_data = await self.calculate_lime_values(insight, instance_idx)

            await self.send_json({
                'status': 'success',
                'type': 'lime_data',
                'data': lime_data
            })

        except Exception as e:
            logger.error(f"Error loading LIME data: {str(e)}")
            await self.send_json({
                'status': 'error',
                'message': str(e)
            })

    @database_sync_to_async
    def get_insight(self):
        """Get insight by ID"""
        try:
            return DataInsight.objects.get(id=self.insight_id)
        except DataInsight.DoesNotExist:
            return None

    @database_sync_to_async
    def calculate_shap_values(self, insight):
        """Calculate SHAP values for insight"""
        try:
            # Retrieve stored SHAP data or calculate if not available
            if hasattr(insight, 'shap_plot_data') and insight.shap_plot_data:
                return insight.shap_plot_data

            # Return feature importance from analysis_data
            if 'summary' in insight.analysis_data:
                summary = insight.analysis_data['summary']
                column_info = summary.get('column_info', {})

                # Create feature importance ranking
                feature_importance = []
                for col, info in column_info.items():
                    importance = 0.0
                    if isinstance(info, dict):
                        if 'std' in info and info['std']:
                            importance = float(info['std'])
                        elif 'unique_values' in info:
                            importance = float(info['unique_values']) / summary.get('rows', 1)

                    feature_importance.append({
                        'feature': col,
                        'importance': importance,
                        'dtype': info.get('dtype', 'unknown') if isinstance(info, dict) else 'unknown'
                    })

                # Sort by importance
                feature_importance.sort(key=lambda x: x['importance'], reverse=True)

                return {
                    'features': feature_importance[:10],
                    'base_value': 0.5,
                    'method': 'statistical'
                }

            return {'error': 'No data available'}

        except Exception as e:
            logger.error(f"Error calculating SHAP values: {str(e)}")
            return {'error': str(e)}

    @database_sync_to_async
    def calculate_lime_values(self, insight, instance_idx):
        """Calculate LIME values for insight"""
        try:
            # Retrieve stored LIME data if available
            if hasattr(insight, 'lime_plot_data') and insight.lime_plot_data:
                return insight.lime_plot_data

            # Return empty LIME structure for now
            return {
                'instance_idx': instance_idx or 0,
                'explanation': [],
                'method': 'lime',
                'status': 'Model required for LIME explanations'
            }

        except Exception as e:
            logger.error(f"Error calculating LIME values: {str(e)}")
            return {'error': str(e)}


# Helper for broadcasting messages to groups
async def send_insight_update(room_group_name, update_data):
    """Helper function to send updates to a WebSocket group"""
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'insight_update',
            'data': update_data
        }
    )
