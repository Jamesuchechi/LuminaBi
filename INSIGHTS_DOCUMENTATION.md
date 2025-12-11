# Insights System Documentation

## Overview

The Insights application provides comprehensive data analysis using statistical methods and machine learning techniques (SHAP/LIME) to help users understand their datasets better.

## Features

### 1. **Data Insights**
Generate automated insights about datasets including:
- Summary statistics
- Data quality assessment
- Distribution analysis
- Anomaly detection
- Pattern discovery

### 2. **Anomaly Detection**
Detect statistical anomalies using:
- Z-score analysis
- Interquartile Range (IQR)
- Local Outlier Factor (LOF)
- Isolation Forest

### 3. **Outlier Analysis**
Identify and analyze outliers with multiple methods:
- Statistical thresholds
- Machine learning-based detection
- Percentage and count reporting

### 4. **Relationship Analysis**
Discover correlations and relationships:
- Pearson correlation
- Relationship strength classification
- Significant relationship identification
- Visual relationship data

### 5. **SHAP/LIME Explanations** (Optional)
When SHAP/LIME libraries are installed:
- Feature importance rankings
- Local interpretable explanations
- Model-agnostic interpretability
- Sample-level explanations

## Models

### DataInsight
Main model for storing insights about datasets.

**Fields:**
- `owner`: User who owns the insight
- `dataset`: Related dataset
- `title`: Insight title
- `insight_type`: Type (summary, relationship, anomaly, pattern, outlier, correlation, distribution, trend)
- `analysis_data`: Complete analysis JSON
- `confidence_score`: 0-1 confidence
- `key_features`: Important features for this insight
- `shap_values`: SHAP explanations (optional)
- `lime_explanation`: LIME explanations (optional)
- `human_explanation`: Readable explanation
- `is_public`: Public visibility flag
- `is_pinned`: Pin for quick access

### AnomalyDetection
Stores detected anomalies in datasets.

**Fields:**
- `dataset`: Related dataset
- `anomaly_type`: Type of anomaly
- `affected_columns`: Columns with anomalies
- `affected_rows`: Row indices of anomalies
- `severity`: low, medium, high, critical
- `anomaly_score`: 0-1 score
- `acknowledged`: Acknowledgement flag

### OutlierAnalysis
Detailed outlier analysis results.

**Fields:**
- `dataset`: Related dataset
- `column`: Column name
- `method`: Detection method (iqr, zscore, isolation_forest, lof)
- `outlier_indices`: Outlier row indices
- `outlier_values`: Actual outlier values
- `outlier_count`: Total outliers
- `outlier_percentage`: Percentage of data

### RelationshipAnalysis
Correlation and relationship analysis.

**Fields:**
- `dataset`: Related dataset
- `feature_1`, `feature_2`: Compared features
- `correlation_coefficient`: -1 to 1
- `p_value`: Statistical p-value
- `is_significant`: Significance flag
- `relationship_type`: linear, non_linear, inverse, no_relationship

### ModelExplanation
SHAP/LIME model explanations.

**Fields:**
- `dataset`: Related dataset
- `model_type`: ML model type
- `target_variable`: Target for prediction
- `shap_summary`: Global SHAP statistics
- `feature_importance`: Feature rankings
- `sample_explanations`: LIME explanations

### InsightReport
Comprehensive report combining insights.

**Fields:**
- `owner`: Report owner
- `dataset`: Related dataset
- `title`: Report title
- `insights`: M2M relation to DataInsight
- `anomalies`: M2M relation to AnomalyDetection
- `summary`: Executive summary
- `key_findings`: Main findings
- `recommendations`: Recommendations

## Services

### InsightGenerator
Main service for generating insights from DataFrames.

```python
from insights.services import InsightGenerator
import pandas as pd

df = pd.read_csv('data.csv')
generator = InsightGenerator(df, dataset_id=1)

# Generate all insights
insights = generator.generate_all_insights()

# Or generate specific insights
summary = generator.generate_summary_statistics()
anomalies = generator.detect_anomalies()
relationships = generator.analyze_relationships()
```

**Methods:**
- `generate_all_insights()`: Complete analysis
- `generate_summary_statistics()`: Basic stats
- `detect_anomalies()`: Anomaly detection
- `detect_outliers()`: Outlier detection
- `analyze_relationships()`: Correlation analysis
- `analyze_distributions()`: Distribution analysis
- `analyze_missing_data()`: Missing data patterns

### SHAPExplainer
SHAP-based feature importance (requires `pip install shap`).

```python
from insights.services import SHAPExplainer

explainer = SHAPExplainer(df)
shap_data = explainer.explain_features(model=your_model)
```

### LIMEExplainer
LIME-based local explanations (requires `pip install lime`).

```python
from insights.services import LIMEExplainer

explainer = LIMEExplainer(df)
explanation = explainer.explain_instance(instance_idx=0, model=your_model)
```

## API Endpoints

### Insight Management
- `GET /insights/` - List all insights
- `GET /insights/insights/<id>/` - Get specific insight
- `POST /insights/datasets/<dataset_id>/generate-insights/` - Generate insights
- `GET /insights/datasets/<dataset_id>/insights/` - Get dataset insights

### Anomalies
- `GET /insights/anomalies/` - List anomalies
- `GET /insights/api/anomalies/` - API list anomalies

### Outliers
- `GET /insights/outliers/` - List outlier analyses
- `GET /insights/api/outliers/` - API list outliers

### REST API
- `GET /insights/api/insights/` - REST API insights
- `GET /insights/api/anomalies/` - REST API anomalies
- `GET /insights/api/outliers/` - REST API outliers

## Usage Workflow

### 1. Upload Dataset
User uploads CSV/Excel file via datasets app.

### 2. Generate Insights
```python
# Via API
POST /insights/datasets/<dataset_id>/generate-insights/

# Response
{
    "status": "success",
    "message": "Insights generated successfully",
    "insight_id": 123,
    "insights_summary": {
        "anomalies_detected": 5,
        "outliers_detected": 3,
        "relationships_found": 8
    }
}
```

### 3. View Results
- Access comprehensive insight dashboard
- Review anomalies and outliers
- Explore relationships and correlations
- Read human-readable explanations

### 4. Create Reports
Combine insights into comprehensive reports with:
- Executive summary
- Key findings
- Recommendations
- Visual analysis

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Optional (for SHAP/LIME):
```bash
pip install shap lime
```

### Setup
1. Add 'insights' to INSTALLED_APPS
2. Run migrations: `python manage.py migrate insights`
3. Admin interface: `python manage.py createsuperuser`

## Configuration

### Settings
Add to `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'insights',
    ...
]

# Optional: Configure insight generation
INSIGHTS_CONFIG = {
    'enable_shap': True,
    'enable_lime': True,
    'anomaly_zscore_threshold': 3,
    'correlation_threshold': 0.3,
    'max_samples_lime': 1000,
}
```

## Performance

### Large Datasets
For datasets with millions of rows:
1. Sample data for analysis
2. Use batch processing
3. Cache results
4. Optimize DataFrame operations

### Query Optimization
- Use select_related() for foreign keys
- Use prefetch_related() for M2M
- Index frequently queried fields
- Use pagination

## Security

### Access Control
- Insights tied to dataset owner
- User can only see own insights
- API enforces permission checks
- Public/private visibility control

### Data Protection
- No data export in free tier
- Encrypted analysis storage
- Audit logging
- GDPR compliance

## Troubleshooting

### SHAP Not Available
```python
# Install SHAP
pip install shap

# Check if available
from insights.services import SHAPExplainer
explainer = SHAPExplainer(df)
if explainer.available:
    print("SHAP ready")
```

### Out of Memory
- Reduce dataset size
- Sample large datasets
- Use chunked processing
- Increase server resources

### Slow Analysis
- Check dataset size
- Optimize column selection
- Use cached results
- Profile with Django Debug Toolbar

## Future Enhancements

1. **Advanced ML Models**
   - Neural networks
   - Gradient boosting
   - Ensemble methods

2. **Real-time Streaming**
   - Continuous monitoring
   - Alerting system
   - Live dashboards

3. **Causal Analysis**
   - Causal inference
   - Treatment effects
   - Intervention analysis

4. **NLP Integration**
   - Text field analysis
   - Sentiment analysis
   - Topic modeling

5. **Automated Reports**
   - Scheduled generation
   - Email distribution
   - PDF export

## Support

For issues or questions:
1. Check this documentation
2. Review code examples
3. Check admin interface
4. Review logs in `/logs/`
5. Contact development team
