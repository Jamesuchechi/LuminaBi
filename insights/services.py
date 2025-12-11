"""
Insights generation service using SHAP, LIME, and statistical analysis
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Main service for generating insights from datasets
    Uses SHAP, LIME, and statistical methods
    """
    
    def __init__(self, df: pd.DataFrame, dataset_id: int = None):
        self.df = df
        self.dataset_id = dataset_id
        self.insights = []
        self.anomalies = []
        self.outliers = {}
        self.relationships = []
    
    def generate_all_insights(self) -> Dict[str, Any]:
        """
        Generate comprehensive insights for the dataset
        """
        try:
            result = {
                'summary_stats': self.generate_summary_statistics(),
                'anomalies': self.detect_anomalies(),
                'outliers': self.detect_outliers(),
                'relationships': self.analyze_relationships(),
                'distributions': self.analyze_distributions(),
                'missing_data': self.analyze_missing_data(),
            }
            return result
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {'error': str(e)}
    
    def generate_summary_statistics(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the dataset
        """
        summary = {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'memory_usage': self.df.memory_usage(deep=True).sum() / 1024 ** 2,  # MB
            'column_info': {},
        }
        
        for col in self.df.columns:
            col_data = {
                'dtype': str(self.df[col].dtype),
                'null_count': int(self.df[col].isnull().sum()),
                'null_percentage': float(self.df[col].isnull().sum() / len(self.df) * 100),
                'unique_values': int(self.df[col].nunique()),
            }
            
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_data.update({
                    'mean': float(self.df[col].mean()) if not self.df[col].isnull().all() else None,
                    'median': float(self.df[col].median()) if not self.df[col].isnull().all() else None,
                    'std': float(self.df[col].std()) if not self.df[col].isnull().all() else None,
                    'min': float(self.df[col].min()) if not self.df[col].isnull().all() else None,
                    'max': float(self.df[col].max()) if not self.df[col].isnull().all() else None,
                    'q1': float(self.df[col].quantile(0.25)) if not self.df[col].isnull().all() else None,
                    'q3': float(self.df[col].quantile(0.75)) if not self.df[col].isnull().all() else None,
                })
            else:
                col_data['top_values'] = self.df[col].value_counts().head(5).to_dict()
            
            summary['column_info'][col] = col_data
        
        return summary
    
    def detect_anomalies(self) -> Dict[str, Any]:
        """
        Detect anomalies using multiple methods
        """
        anomalies = {}
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = self.df[col].dropna()
            if len(col_data) < 3:
                continue
            
            # Z-score anomalies
            z_scores = np.abs(stats.zscore(col_data))
            z_anomalies = np.where(z_scores > 3)[0]
            
            # IQR anomalies
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            iqr_lower = Q1 - 1.5 * IQR
            iqr_upper = Q3 + 1.5 * IQR
            iqr_anomalies = np.where((col_data < iqr_lower) | (col_data > iqr_upper))[0]
            
            combined_anomalies = np.unique(np.concatenate([z_anomalies, iqr_anomalies]))
            
            if len(combined_anomalies) > 0:
                anomalies[col] = {
                    'count': int(len(combined_anomalies)),
                    'percentage': float(len(combined_anomalies) / len(col_data) * 100),
                    'indices': combined_anomalies.tolist()[:100],  # Limit to 100
                    'values': col_data.iloc[combined_anomalies].tolist()[:100],
                    'severity': self._classify_severity(len(combined_anomalies) / len(col_data)),
                }
        
        return anomalies
    
    def detect_outliers(self) -> Dict[str, Any]:
        """
        Detect outliers using Isolation Forest and LOF
        """
        outliers = {}
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return outliers
        
        # Prepare data
        X = self.df[numeric_cols].fillna(self.df[numeric_cols].mean())
        
        if len(X) < 10:
            return outliers
        
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        iso_predictions = iso_forest.fit_predict(X)
        iso_outliers = np.where(iso_predictions == -1)[0]
        
        # Local Outlier Factor
        lof = LocalOutlierFactor(n_neighbors=min(20, len(X) - 1))
        lof_predictions = lof.fit_predict(X)
        lof_outliers = np.where(lof_predictions == -1)[0]
        
        # Combine results
        combined_outliers = np.unique(np.concatenate([iso_outliers, lof_outliers]))
        
        outliers['summary'] = {
            'total_outliers': int(len(combined_outliers)),
            'outlier_percentage': float(len(combined_outliers) / len(X) * 100),
            'methods_used': ['Isolation Forest', 'Local Outlier Factor'],
        }
        
        outliers['outlier_indices'] = combined_outliers.tolist()[:200]  # Limit to 200
        
        return outliers
    
    def analyze_relationships(self) -> Dict[str, Any]:
        """
        Analyze relationships and correlations between columns
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {}
        
        relationships = {}
        corr_matrix = self.df[numeric_cols].corr()
        
        # Find significant correlations
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                corr = corr_matrix.loc[col1, col2]
                
                if abs(corr) > 0.3:  # Threshold for significance
                    key = f"{col1}__{col2}"
                    relationships[key] = {
                        'feature_1': col1,
                        'feature_2': col2,
                        'correlation': float(corr),
                        'strength': self._classify_correlation_strength(abs(corr)),
                        'direction': 'positive' if corr > 0 else 'negative',
                    }
        
        return relationships
    
    def analyze_distributions(self) -> Dict[str, Any]:
        """
        Analyze distributions of columns
        """
        distributions = {}
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = self.df[col].dropna()
            
            # Normality test
            _, p_value = stats.normaltest(col_data) if len(col_data) > 20 else (None, None)
            
            distributions[col] = {
                'skewness': float(stats.skew(col_data)) if len(col_data) > 2 else 0,
                'kurtosis': float(stats.kurtosis(col_data)) if len(col_data) > 3 else 0,
                'is_normal': bool(p_value > 0.05) if p_value is not None else None,
                'distribution_type': self._classify_distribution(col_data),
            }
        
        return distributions
    
    def analyze_missing_data(self) -> Dict[str, Any]:
        """
        Analyze missing data patterns
        """
        missing = {}
        
        total_cells = len(self.df) * len(self.df.columns)
        total_missing = self.df.isnull().sum().sum()
        
        missing['total_missing_percentage'] = float(total_missing / total_cells * 100) if total_cells > 0 else 0
        
        col_missing = self.df.isnull().sum()
        col_missing_pct = (col_missing / len(self.df) * 100).sort_values(ascending=False)
        
        missing['by_column'] = col_missing_pct.to_dict()
        missing['columns_with_missing'] = [col for col in col_missing_pct.index if col_missing_pct[col] > 0]
        
        return missing
    
    @staticmethod
    def _classify_severity(ratio: float) -> str:
        """Classify severity based on anomaly ratio"""
        if ratio > 0.1:
            return 'critical'
        elif ratio > 0.05:
            return 'high'
        elif ratio > 0.02:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _classify_correlation_strength(correlation: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            return 'strong'
        elif abs_corr > 0.5:
            return 'moderate'
        else:
            return 'weak'
    
    @staticmethod
    def _classify_distribution(data: pd.Series) -> str:
        """Classify distribution type"""
        skewness = stats.skew(data)
        
        if abs(skewness) < 0.5:
            return 'symmetric'
        elif skewness > 0:
            return 'right_skewed'
        else:
            return 'left_skewed'


class SHAPExplainer:
    """
    SHAP value calculator for feature importance and explanations
    Requires: shap library (optional)
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        try:
            import shap
            self.shap = shap
            self.available = True
        except ImportError:
            logger.warning("SHAP not installed. Install with: pip install shap")
            self.available = False
    
    def explain_features(self, model=None) -> Dict[str, Any]:
        """
        Generate SHAP explanations for features
        """
        if not self.available or model is None:
            return {'error': 'SHAP not available or model not provided'}
        
        try:
            explainer = self.shap.TreeExplainer(model)
            shap_values = explainer.shap_values(self.df)
            
            return {
                'shap_values': shap_values,
                'base_value': explainer.expected_value,
                'feature_names': self.df.columns.tolist(),
            }
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {str(e)}")
            return {'error': str(e)}


class LIMEExplainer:
    """
    LIME explanations for local interpretability
    Requires: lime library (optional)
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        try:
            import lime.tabular
            self.lime = lime.tabular
            self.available = True
        except ImportError:
            logger.warning("LIME not installed. Install with: pip install lime")
            self.available = False
    
    def explain_instance(self, instance_idx: int, model=None, num_features: int = 10) -> Dict[str, Any]:
        """
        Generate LIME explanation for a specific instance
        """
        if not self.available or model is None:
            return {'error': 'LIME not available or model not provided'}
        
        try:
            explainer = self.lime.LimeTabularExplainer(
                self.df.values,
                feature_names=self.df.columns.tolist(),
                mode='classification'
            )
            
            exp = explainer.explain_instance(
                self.df.iloc[instance_idx].values,
                model.predict_proba,
                num_features=num_features
            )
            
            return {
                'instance_idx': instance_idx,
                'explanation': exp.as_list(),
                'predicted_class': exp.predicted_label,
            }
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {str(e)}")
            return {'error': str(e)}


class SHAPVisualizer:
    """
    Generates SHAP visualization data for JSON serialization
    Converts SHAP explanations into formats suitable for frontend rendering
    """

    @staticmethod
    def generate_summary_plot_data(shap_values, feature_names, feature_values=None) -> Dict[str, Any]:
        """
        Generate SHAP summary plot data (bar plot of mean absolute SHAP values)
        """
        try:
            if isinstance(shap_values, list):
                # Handle binary classification
                shap_vals = np.array(shap_values[0]) if len(shap_values) > 0 else np.array([])
            else:
                shap_vals = np.array(shap_values)

            if shap_vals.size == 0:
                return {'error': 'No SHAP values available'}

            # Calculate mean absolute SHAP values
            if len(shap_vals.shape) > 1:
                mean_abs_shap = np.abs(shap_vals).mean(axis=0)
            else:
                mean_abs_shap = np.abs(shap_vals)

            # Create bar plot data
            plot_data = []
            for i, feature in enumerate(feature_names):
                if i < len(mean_abs_shap):
                    plot_data.append({
                        'feature': feature,
                        'importance': float(mean_abs_shap[i]),
                        'index': i
                    })

            # Sort by importance
            plot_data.sort(key=lambda x: x['importance'], reverse=True)

            return {
                'type': 'bar',
                'title': 'Mean Absolute SHAP Values',
                'description': 'Average impact of each feature on model output',
                'data': plot_data[:20],  # Top 20 features
                'method': 'shap'
            }

        except Exception as e:
            logger.error(f"Error generating SHAP summary plot: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def generate_force_plot_data(shap_value, base_value, feature_values, feature_names, instance_idx=0) -> Dict[str, Any]:
        """
        Generate SHAP force plot data (waterfall effect visualization)
        """
        try:
            # Convert to numpy arrays
            shap_vals = np.array(shap_value).flatten()
            feat_vals = np.array(feature_values).flatten()

            if len(shap_vals) != len(feature_names):
                return {'error': 'Feature count mismatch'}

            # Create force plot data structure
            plot_data = []
            current_value = float(base_value)

            # Sort by absolute SHAP value
            indices = np.argsort(np.abs(shap_vals))[::-1]

            for idx in indices:
                if idx < len(feature_names):
                    shap_contribution = float(shap_vals[idx])
                    feature_value = float(feat_vals[idx]) if idx < len(feat_vals) else None

                    plot_data.append({
                        'feature': feature_names[idx],
                        'value': feature_value,
                        'contribution': shap_contribution,
                        'cumulative': current_value + shap_contribution,
                        'direction': 'positive' if shap_contribution > 0 else 'negative'
                    })

                    current_value += shap_contribution

            return {
                'type': 'waterfall',
                'title': f'SHAP Force Plot - Instance {instance_idx}',
                'description': 'How each feature contributes to the prediction',
                'base_value': float(base_value),
                'final_value': current_value,
                'data': plot_data,
                'method': 'shap_force'
            }

        except Exception as e:
            logger.error(f"Error generating SHAP force plot: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def generate_dependence_plot_data(shap_values, X_data, feature_name, feature_idx, feature_names) -> Dict[str, Any]:
        """
        Generate SHAP dependence plot data (scatter plot of feature value vs SHAP value)
        """
        try:
            shap_vals = np.array(shap_values).flatten()

            if len(shap_vals) == 0:
                return {'error': 'No SHAP values available'}

            # Get feature values
            if hasattr(X_data, 'iloc'):  # pandas DataFrame
                feature_vals = X_data[feature_name].values
            else:
                feature_vals = X_data[:, feature_idx]

            # Create scatter plot data
            plot_data = []
            for i, (feat_val, shap_val) in enumerate(zip(feature_vals[:1000], shap_vals[:1000])):
                plot_data.append({
                    'x': float(feat_val),
                    'y': float(shap_val),
                    'index': i
                })

            return {
                'type': 'scatter',
                'title': f'SHAP Dependence Plot - {feature_name}',
                'description': f'Dependence of model output on {feature_name}',
                'x_label': feature_name,
                'y_label': 'SHAP Value',
                'data': plot_data,
                'method': 'shap_dependence'
            }

        except Exception as e:
            logger.error(f"Error generating SHAP dependence plot: {str(e)}")
            return {'error': str(e)}


class LIMEVisualizer:
    """
    Generates LIME visualization data for JSON serialization
    Converts LIME explanations into formats suitable for frontend rendering
    """

    @staticmethod
    def generate_explanation_plot_data(explanation_list, predicted_label) -> Dict[str, Any]:
        """
        Generate LIME explanation plot data (horizontal bar chart)
        """
        try:
            plot_data = []

            for feature_name, weight in explanation_list:
                plot_data.append({
                    'feature': feature_name,
                    'weight': float(weight),
                    'direction': 'supports' if weight > 0 else 'opposes',
                    'color': '#00f3ff' if weight > 0 else '#bd00ff'
                })

            # Sort by absolute weight
            plot_data.sort(key=lambda x: abs(x['weight']), reverse=True)

            return {
                'type': 'bar_horizontal',
                'title': f'LIME Explanation - {predicted_label}',
                'description': 'Local feature importance for this prediction',
                'predicted_class': predicted_label,
                'data': plot_data[:15],  # Top 15 features
                'method': 'lime'
            }

        except Exception as e:
            logger.error(f"Error generating LIME explanation plot: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def generate_feature_impact_data(explanations, feature_idx) -> Dict[str, Any]:
        """
        Generate aggregated feature impact across multiple explanations
        """
        try:
            impacts = []

            for exp_idx, explanation_list in enumerate(explanations):
                for feature_name, weight in explanation_list:
                    impacts.append({
                        'explanation_idx': exp_idx,
                        'feature': feature_name,
                        'weight': float(weight)
                    })

            return {
                'type': 'distribution',
                'title': 'LIME Feature Impact Distribution',
                'description': 'How feature impact varies across predictions',
                'data': impacts[:100],  # Limit to 100 points
                'method': 'lime_impact'
            }

        except Exception as e:
            logger.error(f"Error generating LIME feature impact data: {str(e)}")
            return {'error': str(e)}

