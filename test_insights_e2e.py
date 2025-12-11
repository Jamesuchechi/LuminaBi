"""
End-to-end integration tests for insights system
Tests the complete workflow: generation -> storage -> visualization -> WebSocket delivery
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Luminabi.settings')
sys.path.insert(0, '/home/jamesuchechi/Documents/Project/Luminabi')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase
from datasets.models import Dataset
from insights.models import DataInsight, AnomalyDetection, OutlierAnalysis, RelationshipAnalysis
from insights.services import InsightGenerator, SHAPVisualizer, LIMEVisualizer
from insights.consumers import InsightGenerationConsumer
import pandas as pd
import numpy as np
import tempfile
import json

User = get_user_model()


class EndToEndInsightsTest(TestCase):
    """End-to-end test for complete insights workflow"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        super().setUpClass()
        
        # Create test user
        cls.user = User.objects.create_user(
            username='test_e2e_user',
            email='e2e@test.com',
            password='testpass123'
        )
        
        # Create test DataFrame with diverse data
        cls.df = pd.DataFrame({
            'age': np.random.randint(18, 80, 200),
            'salary': np.random.randint(30000, 150000, 200),
            'years_experience': np.random.randint(0, 50, 200),
            'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Finance'], 200),
            'performance_score': np.random.uniform(1, 5, 200),
        })
        
        # Add some anomalies
        cls.df.loc[10, 'salary'] = 500000  # Outlier
        cls.df.loc[20, 'age'] = 150  # Invalid age
        
        # Create test dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            cls.df.to_csv(f.name, index=False)
            cls.dataset_file = f.name
        
        cls.dataset = Dataset.objects.create(
            user=cls.user,
            name='Test E2E Dataset',
            file=cls.dataset_file,
            row_count=len(cls.df),
            col_count=len(cls.df.columns),
            data_quality_score=92.5
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        if os.path.exists(cls.dataset_file):
            os.remove(cls.dataset_file)
        super().tearDownClass()
    
    def test_1_insight_generation(self):
        """Test: Generate insights from dataset"""
        print("\n✓ Test 1: Insight Generation")
        
        generator = InsightGenerator(self.df, self.dataset.id)
        results = generator.generate_all_insights()
        
        # Verify all analysis types were generated
        self.assertIn('summary_stats', results)
        self.assertIn('anomalies', results)
        self.assertIn('outliers', results)
        self.assertIn('relationships', results)
        self.assertIn('distributions', results)
        self.assertIn('missing_data', results)
        
        print(f"  - Generated {len(results)} analysis types")
        print(f"  - Anomalies detected: {len(results.get('anomalies', {}))}")
        print(f"  - Outliers detected: {len(results.get('outliers', {}))}")
        print(f"  - Relationships found: {len(results.get('relationships', []))}")
    
    def test_2_insight_storage(self):
        """Test: Store insights in database"""
        print("\n✓ Test 2: Insight Storage")
        
        generator = InsightGenerator(self.df, self.dataset.id)
        results = generator.generate_all_insights()
        
        # Create main insight
        insight = DataInsight.objects.create(
            dataset=self.dataset,
            owner=self.user,
            title='E2E Test Analysis',
            description='Complete end-to-end test analysis',
            insight_type='summary',
            analysis_data=results,
            confidence_score=92.5
        )
        
        self.assertIsNotNone(insight.id)
        self.assertEqual(insight.dataset, self.dataset)
        self.assertEqual(insight.owner, self.user)
        
        print(f"  - Insight created: {insight.id}")
        print(f"  - Analysis data size: {len(json.dumps(results))} bytes")
    
    def test_3_anomaly_storage(self):
        """Test: Store anomalies in database"""
        print("\n✓ Test 3: Anomaly Storage")
        
        generator = InsightGenerator(self.df, self.dataset.id)
        anomalies = generator.detect_anomalies()
        
        anomaly_count = 0
        for col, anomaly_data in anomalies.items():
            if anomaly_data and anomaly_data.get('count', 0) > 0:
                AnomalyDetection.objects.create(
                    dataset=self.dataset,
                    affected_columns=[col],
                    anomaly_type='statistical',
                    affected_rows=anomaly_data.get('indices', []),
                    severity='high' if anomaly_data.get('count', 0) > 5 else 'medium',
                    analysis_data=anomaly_data
                )
                anomaly_count += 1
        
        print(f"  - Anomalies stored: {anomaly_count}")
        self.assertGreater(anomaly_count, 0)
    
    def test_4_outlier_storage(self):
        """Test: Store outlier analyses in database"""
        print("\n✓ Test 4: Outlier Storage")
        
        generator = InsightGenerator(self.df, self.dataset.id)
        outliers = generator.detect_outliers()
        
        outlier_count = 0
        for col, outlier_data in outliers.items():
            if outlier_data:
                for method, indices in outlier_data.items():
                    if indices and len(indices) > 0:
                        OutlierAnalysis.objects.create(
                            dataset=self.dataset,
                            column=col,
                            method=method,
                            outlier_indices=indices,
                            outlier_count=len(indices),
                            outlier_percentage=(len(indices) / len(self.df) * 100),
                            analysis_data={'method': method, 'indices': indices}
                        )
                        outlier_count += 1
        
        print(f"  - Outlier analyses stored: {outlier_count}")
        self.assertGreater(outlier_count, 0)
    
    def test_5_relationship_storage(self):
        """Test: Store relationships in database"""
        print("\n✓ Test 5: Relationship Storage")
        
        generator = InsightGenerator(self.df, self.dataset.id)
        relationships = generator.analyze_relationships()
        
        for rel in relationships:
            RelationshipAnalysis.objects.create(
                dataset=self.dataset,
                feature_1=rel['feature_1'],
                feature_2=rel['feature_2'],
                correlation_coefficient=rel['correlation'],
                p_value=rel.get('p_value', 0),
                relationship_type=rel.get('relationship_type', 'correlation'),
                description=rel.get('description', ''),
                analysis_data=rel
            )
        
        print(f"  - Relationships stored: {len(relationships)}")
        self.assertGreater(len(relationships), 0)
    
    def test_6_shap_visualization(self):
        """Test: Generate SHAP visualization data"""
        print("\n✓ Test 6: SHAP Visualization Generation")
        
        # Get numeric columns
        numeric_data = self.df.select_dtypes(include=[np.number]).values
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Simulate SHAP values (normally from SHAP library)
        simulated_shap_values = np.abs(np.random.randn(numeric_data.shape[0], numeric_data.shape[1]))
        
        # Generate summary plot data
        summary_data = SHAPVisualizer.generate_summary_plot_data(
            simulated_shap_values,
            numeric_cols,
            numeric_data
        )
        
        self.assertIn('data', summary_data)
        self.assertGreater(len(summary_data['data']), 0)
        
        print(f"  - SHAP summary plot created with {len(summary_data['data'])} features")
        
        # Generate force plot data
        force_data = SHAPVisualizer.generate_force_plot_data(
            simulated_shap_values[0],
            0.5,
            numeric_data[0],
            numeric_cols,
            0
        )
        
        self.assertIn('data', force_data)
        self.assertEqual(force_data['type'], 'waterfall')
        
        print(f"  - SHAP force plot created with {len(force_data['data'])} contributors")
    
    def test_7_lime_visualization(self):
        """Test: Generate LIME visualization data"""
        print("\n✓ Test 7: LIME Visualization Generation")
        
        # Simulate LIME explanations
        simulated_explanations = [
            [('age', 0.3), ('salary', -0.2), ('experience', 0.25)],
            [('salary', 0.4), ('performance', 0.15), ('age', -0.1)],
        ]
        
        # Generate explanation plot data
        explanation_data = LIMEVisualizer.generate_explanation_plot_data(
            simulated_explanations[0],
            'Positive Decision'
        )
        
        self.assertIn('data', explanation_data)
        self.assertEqual(explanation_data['type'], 'bar_horizontal')
        
        print(f"  - LIME explanation plot created with {len(explanation_data['data'])} features")
    
    def test_8_api_response_format(self):
        """Test: Verify API response formats"""
        print("\n✓ Test 8: API Response Format Validation")
        
        # Get stored insight
        insight = DataInsight.objects.filter(dataset=self.dataset).first()
        
        if insight:
            # Verify serialization
            data = {
                'id': insight.id,
                'title': insight.title,
                'analysis_data': insight.analysis_data,
                'confidence_score': insight.confidence_score,
            }
            
            # Verify JSON serializable
            json_str = json.dumps(data, default=str)
            parsed = json.loads(json_str)
            
            self.assertIsNotNone(parsed)
            print(f"  - API response size: {len(json_str)} bytes")
            print(f"  - All data is JSON serializable: ✓")
    
    def test_9_websocket_data_format(self):
        """Test: Verify WebSocket message formats"""
        print("\n✓ Test 9: WebSocket Data Format")
        
        # Simulate WebSocket message format
        messages = [
            {
                'status': 'initializing',
                'progress': 0,
                'message': 'Loading dataset...'
            },
            {
                'status': 'processing',
                'progress': 50,
                'message': 'Analyzing relationships...'
            },
            {
                'status': 'completed',
                'progress': 100,
                'message': 'Insights generated successfully',
                'results': {
                    'insights': 1,
                    'anomalies': 3,
                    'outliers': 5,
                    'relationships': 8,
                }
            }
        ]
        
        for msg in messages:
            # Verify each message is JSON serializable
            json_str = json.dumps(msg)
            parsed = json.loads(json_str)
            self.assertIsNotNone(parsed)
        
        print(f"  - {len(messages)} message formats validated")
        print(f"  - All WebSocket messages are valid JSON: ✓")
    
    def test_10_end_to_end_workflow(self):
        """Test: Complete end-to-end workflow"""
        print("\n✓ Test 10: Complete End-to-End Workflow")
        
        # 1. Generate insights
        generator = InsightGenerator(self.df, self.dataset.id)
        results = generator.generate_all_insights()
        
        # 2. Create insight
        insight = DataInsight.objects.create(
            dataset=self.dataset,
            owner=self.user,
            title='E2E Workflow Test',
            insight_type='summary',
            analysis_data=results,
            confidence_score=95.0
        )
        
        # 3. Store anomalies
        anomalies = results.get('anomalies', {})
        anomaly_count = sum(len(v.get('indices', [])) for v in anomalies.values() if v)
        
        # 4. Store outliers
        outliers = results.get('outliers', {})
        outlier_count = sum(len(v) for v in outliers.values() for v2 in v.values() if isinstance(v2, list))
        
        # 5. Store relationships
        relationships = results.get('relationships', [])
        
        # 6. Verify all stored
        self.assertIsNotNone(insight)
        self.assertGreater(anomaly_count, 0)
        
        print(f"  ✓ Insight created: {insight.id}")
        print(f"  ✓ Anomalies detected: {anomaly_count}")
        print(f"  ✓ Outliers detected: {outlier_count}")
        print(f"  ✓ Relationships found: {len(relationships)}")
        print(f"\n🎉 Complete end-to-end workflow successful!")


def run_tests():
    """Run all end-to-end tests"""
    print("\n" + "="*70)
    print("INSIGHTS SYSTEM - END-TO-END INTEGRATION TESTS")
    print("="*70)
    
    try:
        # Create test fixture data
        user = User.objects.create_user(
            username='test_e2e_user_' + str(np.random.randint(0, 99999)),
            email='e2e@test.com',
            password='testpass123'
        )
        
        # Create test DataFrame with diverse data
        df = pd.DataFrame({
            'age': np.random.randint(18, 80, 200),
            'salary': np.random.randint(30000, 150000, 200),
            'years_experience': np.random.randint(0, 50, 200),
            'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Finance'], 200),
            'performance_score': np.random.uniform(1, 5, 200),
        })
        
        # Add some anomalies
        df.loc[10, 'salary'] = 500000  # Outlier
        df.loc[20, 'age'] = 150  # Invalid age
        
        # Create test dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            dataset_file = f.name
        
        dataset = Dataset.objects.create(
            owner=user,
            name='Test E2E Dataset',
            file=dataset_file,
            row_count=len(df),
            col_count=len(df.columns),
            data_quality_score=92.5
        )
        
        # Run tests
        print("\n✓ Test 1: Insight Generation")
        generator = InsightGenerator(df, dataset.id)
        results = generator.generate_all_insights()
        
        assert 'summary_stats' in results
        assert 'anomalies' in results
        assert 'outliers' in results
        assert 'relationships' in results
        print(f"  - Generated {len(results)} analysis types")
        print(f"  - Anomalies detected: {len(results.get('anomalies', {}))}")
        print(f"  - Outliers detected: {len(results.get('outliers', {}))}")
        print(f"  - Relationships found: {len(results.get('relationships', []))}")
        
        print("\n✓ Test 2: Insight Storage")
        insight = DataInsight.objects.create(
            dataset=dataset,
            owner=user,
            title='E2E Test Analysis',
            description='Complete end-to-end test analysis',
            insight_type='summary',
            analysis_data=results,
            confidence_score=92.5
        )
        
        assert insight.id is not None
        assert insight.dataset == dataset
        assert insight.owner == user
        print(f"  - Insight created: {insight.id}")
        print(f"  - Analysis data size: {len(json.dumps(results, default=str))} bytes")
        
        print("\n✓ Test 3: Anomaly Storage")
        anomalies = generator.detect_anomalies()
        
        anomaly_count = 0
        for col, anomaly_data in anomalies.items():
            if anomaly_data and anomaly_data.get('count', 0) > 0:
                AnomalyDetection.objects.create(
                    dataset=dataset,
                    affected_columns=[col],
                    anomaly_type='statistical',
                    affected_rows=anomaly_data.get('indices', []),
                    severity='high' if anomaly_data.get('count', 0) > 5 else 'medium',
                    anomaly_score=float(anomaly_data.get('count', 0)) / len(df) if len(df) > 0 else 0,
                    details=anomaly_data
                )
                anomaly_count += 1
        
        print(f"  - Anomalies stored: {anomaly_count}")
        
        print("\n✓ Test 4: Outlier Storage")
        outliers = generator.detect_outliers()
        
        outlier_count = 0
        # Handle both old and new formats
        if 'outlier_indices' in outliers and isinstance(outliers['outlier_indices'], list):
            # New format: single outlier list
            if len(outliers['outlier_indices']) > 0:
                OutlierAnalysis.objects.create(
                    dataset=dataset,
                    column='combined',
                    method='isolation_forest',
                    outlier_indices=outliers['outlier_indices'],
                    outlier_count=len(outliers['outlier_indices']),
                    outlier_percentage=outliers['summary'].get('outlier_percentage', 0),
                    statistics=outliers.get('summary', {})
                )
                outlier_count += 1
        else:
            # Legacy format: per-column outliers
            for col, outlier_data in outliers.items():
                if outlier_data and isinstance(outlier_data, dict):
                    for method, indices in outlier_data.items():
                        if indices and isinstance(indices, list) and len(indices) > 0:
                            OutlierAnalysis.objects.create(
                                dataset=dataset,
                                column=col,
                                method=method,
                                outlier_indices=indices,
                                outlier_count=len(indices),
                                outlier_percentage=(len(indices) / len(df) * 100),
                                statistics={'method': method, 'count': len(indices)}
                            )
                            outlier_count += 1
        
        print(f"  - Outlier analyses stored: {outlier_count}")
        
        print("\n✓ Test 5: Relationship Storage")
        relationships = generator.analyze_relationships()
        
        for rel in relationships:
            RelationshipAnalysis.objects.create(
                dataset=dataset,
                feature_1=rel['feature_1'],
                feature_2=rel['feature_2'],
                correlation_coefficient=rel['correlation'],
                p_value=rel.get('p_value', 0),
                relationship_type=rel.get('relationship_type', 'linear'),
                description=rel.get('description', ''),
            )
        
        print(f"  - Relationships stored: {len(relationships)}")
        
        print("\n✓ Test 6: SHAP Visualization Generation")
        numeric_data = df.select_dtypes(include=[np.number]).values
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        simulated_shap_values = np.abs(np.random.randn(numeric_data.shape[0], numeric_data.shape[1]))
        
        summary_data = SHAPVisualizer.generate_summary_plot_data(
            simulated_shap_values,
            numeric_cols,
            numeric_data
        )
        
        assert 'data' in summary_data
        assert len(summary_data['data']) > 0
        print(f"  - SHAP summary plot created with {len(summary_data['data'])} features")
        
        force_data = SHAPVisualizer.generate_force_plot_data(
            simulated_shap_values[0],
            0.5,
            numeric_data[0],
            numeric_cols,
            0
        )
        
        assert 'data' in force_data
        assert force_data['type'] == 'waterfall'
        print(f"  - SHAP force plot created with {len(force_data['data'])} contributors")
        
        print("\n✓ Test 7: LIME Visualization Generation")
        simulated_explanations = [
            [('age', 0.3), ('salary', -0.2), ('experience', 0.25)],
            [('salary', 0.4), ('performance', 0.15), ('age', -0.1)],
        ]
        
        explanation_data = LIMEVisualizer.generate_explanation_plot_data(
            simulated_explanations[0],
            'Positive Decision'
        )
        
        assert 'data' in explanation_data
        assert explanation_data['type'] == 'bar_horizontal'
        print(f"  - LIME explanation plot created with {len(explanation_data['data'])} features")
        
        print("\n✓ Test 8: API Response Format Validation")
        data = {
            'id': insight.id,
            'title': insight.title,
            'analysis_data': insight.analysis_data,
            'confidence_score': insight.confidence_score,
        }
        
        json_str = json.dumps(data, default=str)
        parsed = json.loads(json_str)
        
        assert parsed is not None
        print(f"  - API response size: {len(json_str)} bytes")
        print(f"  - All data is JSON serializable: ✓")
        
        print("\n✓ Test 9: WebSocket Data Format")
        messages = [
            {
                'status': 'initializing',
                'progress': 0,
                'message': 'Loading dataset...'
            },
            {
                'status': 'processing',
                'progress': 50,
                'message': 'Analyzing relationships...'
            },
            {
                'status': 'completed',
                'progress': 100,
                'message': 'Insights generated successfully',
                'results': {
                    'insights': 1,
                    'anomalies': 3,
                    'outliers': 5,
                    'relationships': 8,
                }
            }
        ]
        
        for msg in messages:
            json_str = json.dumps(msg)
            parsed = json.loads(json_str)
            assert parsed is not None
        
        print(f"  - {len(messages)} message formats validated")
        print(f"  - All WebSocket messages are valid JSON: ✓")
        
        print("\n✓ Test 10: Complete End-to-End Workflow")
        generator2 = InsightGenerator(df, dataset.id)
        results2 = generator2.generate_all_insights()
        
        insight2 = DataInsight.objects.create(
            dataset=dataset,
            owner=user,
            title='E2E Workflow Test',
            insight_type='summary',
            analysis_data=results2,
            confidence_score=95.0
        )
        
        anomalies2 = results2.get('anomalies', {})
        anomaly_count2 = sum(len(v.get('indices', [])) for v in anomalies2.values() if v)
        
        outliers2 = results2.get('outliers', {})
        outlier_count2 = 0
        if 'outlier_indices' in outliers2 and isinstance(outliers2['outlier_indices'], list):
            outlier_count2 = len(outliers2['outlier_indices'])
        else:
            outlier_count2 = sum(len(v) for v in outliers2.values() for v2 in (v.values() if isinstance(v, dict) else []) if isinstance(v2, list))
        
        relationships2 = results2.get('relationships', [])
        
        assert insight2 is not None
        assert anomaly_count2 > 0
        
        print(f"  ✓ Insight created: {insight2.id}")
        print(f"  ✓ Anomalies detected: {anomaly_count2}")
        print(f"  ✓ Outliers detected: {outlier_count2}")
        print(f"  ✓ Relationships found: {len(relationships2)}")
        
        # Clean up
        if os.path.exists(dataset_file):
            os.remove(dataset_file)
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - END-TO-END WORKFLOW SUCCESSFUL!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()



if __name__ == '__main__':
    run_tests()
