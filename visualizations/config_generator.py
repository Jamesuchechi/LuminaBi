"""
Chart Configuration Generator Service
Automatically generates JSON configurations for visualizations based on dataset analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Color scheme for visualizations
COLORS = {
    'primary': ['#00f3ff', '#bd00ff', '#ff00aa', '#00ff9d', '#ffaa00', '#ff6b6b'],
    'secondary': ['rgba(0, 243, 255, 0.8)', 'rgba(189, 0, 255, 0.8)', 'rgba(255, 0, 170, 0.8)', 
                  'rgba(0, 255, 157, 0.8)', 'rgba(255, 170, 0, 0.8)', 'rgba(255, 107, 107, 0.8)'],
    'transparent': ['rgba(0, 243, 255, 0.2)', 'rgba(189, 0, 255, 0.2)', 'rgba(255, 0, 170, 0.2)',
                    'rgba(0, 255, 157, 0.2)', 'rgba(255, 170, 0, 0.2)', 'rgba(255, 107, 107, 0.2)'],
}


class ChartConfigGenerator:
    """Generate Chart.js configurations from datasets"""

    def __init__(self, df: pd.DataFrame, column_names: List[str] = None):
        """
        Initialize with DataFrame
        
        Args:
            df: Pandas DataFrame containing the data
            column_names: List of column names (used when df not available)
        """
        self.df = df
        self.column_names = column_names or (list(df.columns) if df is not None else [])
        self.numeric_columns = self._get_numeric_columns()
        self.categorical_columns = self._get_categorical_columns()

    def _get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns"""
        if self.df is not None:
            return self.df.select_dtypes(include=[np.number]).columns.tolist()
        return []

    def _get_categorical_columns(self) -> List[str]:
        """Get list of categorical/string columns"""
        if self.df is not None:
            return self.df.select_dtypes(include=['object']).columns.tolist()
        return []

    def _normalize_chart_type(self, chart_type: str) -> str:
        """Normalize various incoming chart type names to internal handlers."""
        if not chart_type:
            return 'bar'
        t = chart_type.strip().lower()
        # Accept common aliases
        aliases = {
            'doughnut': 'donut',
            'donut': 'donut',
            'area': 'area',
            'timeseries': 'line',
            'time': 'line',
        }
        return aliases.get(t, t)

    def _sanitize_value(self, v):
        """Return JSON-safe value: convert NaN/inf to None, convert numpy types to native types."""
        try:
            if v is None:
                return None
            if isinstance(v, (float, int)):
                if pd.isna(v) or np.isinf(v):
                    return None
                # convert numpy types to Python scalar
                if isinstance(v, (np.floating, np.integer)):
                    return float(v) if isinstance(v, np.floating) else int(v)
                return v
            # numpy types
            if isinstance(v, (np.integer, np.floating)):
                if np.isnan(v) or np.isinf(v):
                    return None
                return v.item()
            # Pandas NA
            if pd.isna(v):
                return None
        except Exception:
            pass
        # Fallback to string for objects
        try:
            return str(v)
        except Exception:
            return None

    def _sanitize_series(self, series: pd.Series) -> List[Any]:
        """Convert a pandas Series to a JSON-safe Python list."""
        out = []
        for v in series.tolist():
            out.append(self._sanitize_value(v))
        return out

    def _sanitize_point(self, x, y, r=None):
        """Sanitize a scatter/bubble point dict."""
        point = {'x': self._sanitize_value(x), 'y': self._sanitize_value(y)}
        if r is not None:
            point['r'] = self._sanitize_value(r)
        return point

    def generate_config(self, chart_type: str, x_column: str = None, y_columns: List[str] = None,
                        title: str = None, **kwargs) -> Dict[str, Any]:
        """
        Generate chart configuration
        
        Args:
            chart_type: Type of chart ('bar', 'line', 'pie', 'scatter', etc.)
            x_column: Column for X-axis
            y_columns: Columns for Y-axis
            title: Chart title
            **kwargs: Additional options
            
        Returns:
            Chart.js configuration dictionary
        """
        try:
            chart_type_norm = self._normalize_chart_type(chart_type)
            method_name = f'_generate_{chart_type_norm}_config'
            if not hasattr(self, method_name):
                raise ValueError(f"Unsupported chart type: {chart_type_norm}")
            
            method = getattr(self, method_name)
            config = method(x_column=x_column, y_columns=y_columns, title=title, **kwargs)
            
            logger.info(f"Generated {chart_type_norm} configuration")
            return config
        except Exception as e:
            logger.error(f"Error generating {chart_type} config: {str(e)}")
            raise

    def _get_best_columns(self, chart_type: str) -> Tuple[str, List[str]]:
        """
        Suggest best columns for chart type based on data
        
        Args:
            chart_type: Type of chart
            
        Returns:
            Tuple of (x_column, y_columns)
        """
        if chart_type in ['pie', 'donut']:
            # For pie charts, use first categorical and first numeric
            if self.categorical_columns and self.numeric_columns:
                return self.categorical_columns[0], [self.numeric_columns[0]]
            elif self.numeric_columns:
                return None, self.numeric_columns[:1]
        elif chart_type in ['bar', 'line', 'area', 'scatter']:
            # For these, prefer categorical X and numeric Y
            if self.categorical_columns and self.numeric_columns:
                return self.categorical_columns[0], [self.numeric_columns[0]]
            elif len(self.numeric_columns) >= 2:
                return self.numeric_columns[0], self.numeric_columns[1:]
            elif self.numeric_columns:
                return None, self.numeric_columns[:1]
        elif chart_type in ['heatmap', 'bubble', 'radar']:
            # For these, use all numeric columns
            return None, self.numeric_columns[:5]  # Limit to 5 columns
        
        return None, self.numeric_columns[:1] if self.numeric_columns else []

    def _get_data_samples(self, column: str, limit: int = 10) -> List[Any]:
        """Get sample values from a column"""
        if self.df is not None and column in self.df.columns:
            return self.df[column].head(limit).tolist()
        return []

    def _generate_bar_config(self, x_column: str = None, y_columns: List[str] = None,
                             title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate bar chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('bar')
        
        if self.df is None:
            return self._empty_bar_config(title or "Bar Chart")

        labels = self.df[x_col].astype(str).tolist() if x_col else list(range(len(self.df)))
        
        datasets = []
        for idx, y_col in enumerate(y_cols):
            datasets.append({
                'label': str(y_col),
                'data': self._sanitize_series(self.df[y_col]),
                'backgroundColor': COLORS['primary'][idx % len(COLORS['primary'])],
                'borderColor': COLORS['secondary'][idx % len(COLORS['secondary'])],
                'borderWidth': 2,
                'borderRadius': 4,
            })

        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': datasets,
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Bar Chart - {', '.join(y_cols)}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
                'scales': {
                    'x': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                    'y': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                },
            },
        }

    def _generate_line_config(self, x_column: str = None, y_columns: List[str] = None,
                              title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate line chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('line')
        
        if self.df is None:
            return self._empty_line_config(title or "Line Chart")

        labels = self.df[x_col].astype(str).tolist() if x_col else list(range(len(self.df)))
        
        datasets = []
        for idx, y_col in enumerate(y_cols):
            datasets.append({
                'label': str(y_col),
                'data': self._sanitize_series(self.df[y_col]),
                'borderColor': COLORS['primary'][idx % len(COLORS['primary'])],
                'backgroundColor': COLORS['transparent'][idx % len(COLORS['transparent'])],
                'borderWidth': 2,
                'fill': True,
                'tension': 0.4,
                'pointRadius': 4,
                'pointBackgroundColor': COLORS['primary'][idx % len(COLORS['primary'])],
                'pointBorderColor': '#ffffff',
                'pointBorderWidth': 2,
            })

        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': datasets,
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Line Chart - {', '.join(y_cols)}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
                'scales': {
                    'x': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                    'y': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                },
            },
        }

    def _generate_pie_config(self, x_column: str = None, y_columns: List[str] = None,
                             title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate pie chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('pie')
        
        if self.df is None:
            return self._empty_pie_config(title or "Pie Chart")

        labels = self.df[x_col].astype(str).tolist() if x_col else [f"Slice {i}" for i in range(len(self.df))]
        data = self._sanitize_series(self.df[y_cols[0]])

        return {
            'type': 'pie',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': str(y_cols[0]),
                        'data': data,
                        'backgroundColor': COLORS['primary'],
                        'borderColor': '#ffffff',
                        'borderWidth': 2,
                    }
                ],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Pie Chart - {y_cols[0]}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
            },
        }

    def _generate_scatter_config(self, x_column: str = None, y_columns: List[str] = None,
                                 title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate scatter chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('scatter')
        
        if self.df is None:
            return self._empty_scatter_config(title or "Scatter Chart")

        datasets = []
        for idx, y_col in enumerate(y_cols):
            data_points = []
            for i in range(len(self.df)):
                data_points.append(self._sanitize_point(
                    self.df.iloc[i][x_col] if x_col else i,
                    self.df.iloc[i][y_col]
                ))
            
            datasets.append({
                'label': str(y_col),
                'data': data_points,
                'backgroundColor': COLORS['secondary'][idx % len(COLORS['secondary'])],
                'borderColor': COLORS['primary'][idx % len(COLORS['primary'])],
                'borderWidth': 2,
                'pointRadius': 6,
            })

        return {
            'type': 'scatter',
            'data': {'datasets': datasets},
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Scatter Chart - {x_col} vs {', '.join(y_cols)}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
                'scales': {
                    'x': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                    'y': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                },
            },
        }

    def _generate_area_config(self, x_column: str = None, y_columns: List[str] = None,
                              title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate area chart configuration"""
        # Area charts are similar to line charts but with fill
        return self._generate_line_config(x_column, y_columns, title, **kwargs)

    def _generate_radar_config(self, x_column: str = None, y_columns: List[str] = None,
                               title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate radar chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('radar')
        
        if self.df is None:
            return self._empty_radar_config(title or "Radar Chart")

        labels = self.df[x_col].astype(str).tolist() if x_col else list(range(len(self.df)))
        
        datasets = []
        for idx, y_col in enumerate(y_cols):
            datasets.append({
                'label': str(y_col),
                'data': self._sanitize_series(self.df[y_col]),
                'borderColor': COLORS['primary'][idx % len(COLORS['primary'])],
                'backgroundColor': COLORS['transparent'][idx % len(COLORS['transparent'])],
                'borderWidth': 2,
                'pointRadius': 4,
                'pointBackgroundColor': COLORS['primary'][idx % len(COLORS['primary'])],
            })

        return {
            'type': 'radar',
            'data': {
                'labels': labels,
                'datasets': datasets,
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Radar Chart - {', '.join(y_cols)}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
                'scales': {
                    'r': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                },
            },
        }

    def _generate_heatmap_config(self, x_column: str = None, y_columns: List[str] = None,
                                 title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate heatmap configuration (using Chart.js bubble as approximation)"""
        if self.df is None:
            return self._empty_bar_config(title or "Heatmap")
        
        # For heatmap, we'll create a matrix visualization
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('heatmap')
        
        # Create pivot table for heatmap
        if len(y_cols) >= 2:
            pivot = self.df.pivot_table(
                values=y_cols[1] if len(y_cols) > 1 else y_cols[0],
                index=x_col if x_col else self.df.index,
                columns=y_cols[0],
                aggfunc='sum'
            )
        else:
            pivot = self.df.set_index(x_col if x_col else self.df.index)[y_cols]
        
        # Convert to bar chart as fallback (Chart.js doesn't have native heatmap)
        return self._generate_bar_config(x_column, y_columns, title, **kwargs)

    def _generate_bubble_config(self, x_column: str = None, y_columns: List[str] = None,
                                title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate bubble chart configuration"""
        if self.df is None or len(self.numeric_columns) < 3:
            return self._empty_scatter_config(title or "Bubble Chart")
        
        x_col = x_column or self.numeric_columns[0]
        y_col = y_columns[0] if y_columns else self.numeric_columns[1]
        r_col = self.numeric_columns[2]
        
        data_points = []
        for i in range(len(self.df)):
            r_val = abs(self._sanitize_value(self.df.iloc[i][r_col]) or 1)
            data_points.append(self._sanitize_point(
                self.df.iloc[i][x_col],
                self.df.iloc[i][y_col],
                r_val / 10  # Scale radius
            ))
        
        return {
            'type': 'bubble',
            'data': {
                'datasets': [
                    {
                        'label': f"{y_col} vs {x_col}",
                        'data': data_points,
                        'backgroundColor': COLORS['secondary'][0],
                        'borderColor': COLORS['primary'][0],
                        'borderWidth': 2,
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Bubble Chart - {x_col} vs {y_col} (size: {r_col})",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
                'scales': {
                    'x': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                    'y': {
                        'ticks': {'color': '#ffffff'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'},
                    },
                },
            },
        }

    def _generate_donut_config(self, x_column: str = None, y_columns: List[str] = None,
                               title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate donut chart configuration"""
        x_col, y_cols = x_column or None, y_columns or []
        
        if not x_col or not y_cols:
            x_col, y_cols = self._get_best_columns('donut')
        
        if self.df is None:
            return self._empty_pie_config(title or "Donut Chart")

        labels = self.df[x_col].astype(str).tolist() if x_col else [f"Slice {i}" for i in range(len(self.df))]
        data = self._sanitize_series(self.df[y_cols[0]])

        return {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': str(y_cols[0]),
                        'data': data,
                        'backgroundColor': COLORS['primary'],
                        'borderColor': '#ffffff',
                        'borderWidth': 2,
                    }
                ],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or f"Donut Chart - {y_cols[0]}",
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                    'legend': {
                        'display': True,
                        'labels': {'color': '#ffffff'},
                    },
                },
            },
        }

    def _generate_treemap_config(self, x_column: str = None, y_columns: List[str] = None,
                                 title: str = None, **kwargs) -> Dict[str, Any]:
        """Generate treemap configuration (using bubble as fallback)"""
        # Chart.js doesn't have treemap, so we fallback to bar
        return self._generate_bar_config(x_column, y_columns, title, **kwargs)

    # Empty chart configs for when data is not available
    def _empty_bar_config(self, title: str) -> Dict[str, Any]:
        """Empty bar chart configuration"""
        return {
            'type': 'bar',
            'data': {
                'labels': ['No Data', 'Available'],
                'datasets': [
                    {
                        'label': 'Sample Data',
                        'data': [0, 0],
                        'backgroundColor': COLORS['primary'],
                    }
                ],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                },
            },
        }

    def _empty_line_config(self, title: str) -> Dict[str, Any]:
        """Empty line chart configuration"""
        return {
            'type': 'line',
            'data': {
                'labels': ['No Data', 'Available'],
                'datasets': [
                    {
                        'label': 'Sample Data',
                        'data': [0, 0],
                        'borderColor': COLORS['primary'][0],
                        'backgroundColor': COLORS['transparent'][0],
                    }
                ],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                },
            },
        }

    def _empty_pie_config(self, title: str) -> Dict[str, Any]:
        """Empty pie chart configuration"""
        return {
            'type': 'pie',
            'data': {
                'labels': ['No Data'],
                'datasets': [
                    {
                        'label': 'Sample Data',
                        'data': [100],
                        'backgroundColor': [COLORS['primary'][0]],
                    }
                ],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                },
            },
        }

    def _empty_scatter_config(self, title: str) -> Dict[str, Any]:
        """Empty scatter chart configuration"""
        return {
            'type': 'scatter',
            'data': {
                'datasets': [
                    {
                        'label': 'Sample Data',
                        'data': [{'x': 0, 'y': 0}],
                        'backgroundColor': COLORS['secondary'][0],
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                },
            },
        }

    def _empty_radar_config(self, title: str) -> Dict[str, Any]:
        """Empty radar chart configuration"""
        return {
            'type': 'radar',
            'data': {
                'labels': ['No Data'],
                'datasets': [
                    {
                        'label': 'Sample Data',
                        'data': [0],
                        'backgroundColor': COLORS['transparent'][0],
                        'borderColor': COLORS['primary'][0],
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 16, 'weight': 'bold'},
                        'color': '#ffffff',
                    },
                },
            },
        }

    def suggest_best_chart_type(self) -> str:
        """
        Suggest the best chart type based on data characteristics
        
        Returns:
            Suggested chart type
        """
        # If mostly categorical, use bar
        if len(self.categorical_columns) > len(self.numeric_columns):
            return 'bar'
        
        # If time series data, use line
        if len(self.numeric_columns) >= 2:
            return 'line'
        
        # If few unique categories, use pie
        if self.categorical_columns and self.df is not None:
            unique_count = self.df[self.categorical_columns[0]].nunique()
            if unique_count <= 10:
                return 'pie'
        
        # Default to bar
        return 'bar'

    def get_recommended_config(self, title: str = None) -> Dict[str, Any]:
        """
        Get recommended chart configuration based on data analysis
        
        Args:
            title: Optional chart title
            
        Returns:
            Chart configuration dictionary
        """
        chart_type = self.suggest_best_chart_type()
        return self.generate_config(chart_type, title=title or "Auto-Generated Chart")
