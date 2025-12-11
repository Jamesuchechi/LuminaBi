"""
Tests for insights app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from datasets.models import Dataset
from .models import DataInsight, AnomalyDetection
from .services import InsightGenerator
import pandas as pd
import tempfile
import os

User = get_user_model()


class InsightGeneratorTestCase(TestCase):
    """Test insight generation service"""
    
    def setUp(self):
        """Create test data"""
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        
        # Create test dataframe
        self.df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5, 100],  # Contains outlier
            'B': [2, 4, 6, 8, 10, 200],
            'C': ['cat', 'dog', 'cat', 'dog', 'bird', 'fish'],
        })
    
    def test_summary_statistics(self):
        """Test summary statistics generation"""
        generator = InsightGenerator(self.df)
        summary = generator.generate_summary_statistics()
        
        self.assertEqual(summary['rows'], 6)
        self.assertEqual(summary['columns'], 3)
        self.assertIn('column_info', summary)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        generator = InsightGenerator(self.df)
        anomalies = generator.detect_anomalies()
        
        self.assertIn('A', anomalies)  # Should detect outlier in column A
        self.assertGreater(anomalies['A']['count'], 0)
    
    def test_relationship_analysis(self):
        """Test relationship analysis"""
        generator = InsightGenerator(self.df)
        relationships = generator.analyze_relationships()
        
        # A and B should have strong positive correlation
        self.assertGreater(len(relationships), 0)


class DataInsightModelTestCase(TestCase):
    """Test DataInsight model"""
    
    def setUp(self):
        """Create test data"""
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.dataset = Dataset.objects.create(
            owner=self.user,
            name='Test Dataset',
            file_type='csv'
        )
    
    def test_create_insight(self):
        """Test creating insight"""
        insight = DataInsight.objects.create(
            owner=self.user,
            dataset=self.dataset,
            title='Test Insight',
            insight_type='summary',
            analysis_data={'test': 'data'},
        )
        
        self.assertEqual(insight.title, 'Test Insight')
        self.assertEqual(insight.owner, self.user)
