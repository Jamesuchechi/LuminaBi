"""
Data Visualization Service using Plotly
Creates interactive visualizations from datasets
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Color scheme for consistent theme
PLOTLY_COLORS = {
    'background': '#030014',
    'paper_bg': '#0f0a20',
    'font_color': '#ffffff',
    'grid_color': '#2a1f4e',
    'neon_blue': '#00f3ff',
    'neon_purple': '#bd00ff',
    'neon_pink': '#ff00aa',
    'neon_green': '#00ff9d',
}


class VisualizationEngine:
    """Create visualizations using Plotly"""

    def __init__(self, df: pd.DataFrame):
        """Initialize with DataFrame"""
        self.df = df
        self._apply_theme = self._get_theme()

    def _get_theme(self) -> Dict[str, Any]:
        """Get dark theme configuration"""
        return {
            'template': 'plotly_dark',
            'plot_bgcolor': PLOTLY_COLORS['background'],
            'paper_bgcolor': PLOTLY_COLORS['background'],
            'font_color': PLOTLY_COLORS['font_color'],
            'showlegend': True,
        }

    def create_line_chart(
        self,
        x_column: str,
        y_columns: List[str],
        title: str = 'Line Chart',
        **kwargs
    ) -> go.Figure:
        """Create line chart"""
        fig = go.Figure()

        for y_col in y_columns:
            fig.add_trace(go.Scatter(
                x=self.df[x_column],
                y=self.df[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(width=2),
            ))

        fig.update_layout(
            title=title,
            xaxis_title=x_column,
            yaxis_title='Value',
            hovermode='x unified',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
        )

        return fig

    def create_bar_chart(
        self,
        x_column: str,
        y_columns: List[str],
        title: str = 'Bar Chart',
        barmode: str = 'group',
        **kwargs
    ) -> go.Figure:
        """Create bar chart"""
        fig = go.Figure()

        for y_col in y_columns:
            fig.add_trace(go.Bar(
                x=self.df[x_column],
                y=self.df[y_col],
                name=y_col,
            ))

        fig.update_layout(
            title=title,
            xaxis_title=x_column,
            yaxis_title='Value',
            barmode=barmode,
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
            hovermode='x unified',
        )

        return fig

    def create_histogram(
        self,
        column: str,
        nbins: int = 30,
        title: str = 'Histogram',
        **kwargs
    ) -> go.Figure:
        """Create histogram"""
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=self.df[column],
            nbinsx=nbins,
            name=column,
            marker=dict(color=PLOTLY_COLORS['neon_blue']),
        ))

        fig.update_layout(
            title=title,
            xaxis_title=column,
            yaxis_title='Frequency',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
            showlegend=False,
        )

        return fig

    def create_scatter_plot(
        self,
        x_column: str,
        y_column: str,
        title: str = 'Scatter Plot',
        size_column: Optional[str] = None,
        color_column: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Create scatter plot"""
        fig = go.Figure()

        scatter_kwargs = {
            'x': self.df[x_column],
            'y': self.df[y_column],
            'mode': 'markers',
            'name': f'{x_column} vs {y_column}',
        }

        if size_column and size_column in self.df.columns:
            scatter_kwargs['marker'] = dict(
                size=self.df[size_column] / self.df[size_column].max() * 20,
            )

        if color_column and color_column in self.df.columns:
            scatter_kwargs['marker'] = dict(
                color=self.df[color_column],
                colorscale='Viridis',
                showscale=True,
            )

        fig.add_trace(go.Scatter(**scatter_kwargs))

        fig.update_layout(
            title=title,
            xaxis_title=x_column,
            yaxis_title=y_column,
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
            hovermode='closest',
        )

        return fig

    def create_pie_chart(
        self,
        column: str,
        title: str = 'Pie Chart',
        top_n: int = 10,
        **kwargs
    ) -> go.Figure:
        """Create pie chart"""
        value_counts = self.df[column].value_counts().head(top_n)

        fig = go.Figure(data=[go.Pie(
            labels=value_counts.index,
            values=value_counts.values,
            marker=dict(line=dict(color=PLOTLY_COLORS['background'], width=2)),
        )])

        fig.update_layout(
            title=title,
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
        )

        return fig

    def create_heatmap(
        self,
        columns: Optional[List[str]] = None,
        title: str = 'Heatmap',
        **kwargs
    ) -> go.Figure:
        """Create correlation heatmap"""
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()

        corr_matrix = self.df[columns].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='Viridis',
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text:.2f}',
            textfont={'size': 10},
        ))

        fig.update_layout(
            title=title,
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
        )

        return fig

    def create_boxplot(
        self,
        columns: Optional[List[str]] = None,
        title: str = 'Box Plot',
        **kwargs
    ) -> go.Figure:
        """Create box plot for numeric columns"""
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()

        fig = go.Figure()

        for col in columns[:10]:  # Limit to first 10 columns
            fig.add_trace(go.Box(
                y=self.df[col],
                name=col,
            ))

        fig.update_layout(
            title=title,
            yaxis_title='Value',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
            hovermode='closest',
        )

        return fig

    def create_area_chart(
        self,
        x_column: str,
        y_columns: List[str],
        title: str = 'Area Chart',
        **kwargs
    ) -> go.Figure:
        """Create area chart"""
        fig = go.Figure()

        for y_col in y_columns:
            fig.add_trace(go.Scatter(
                x=self.df[x_column],
                y=self.df[y_col],
                fill='tonexty',
                name=y_col,
                line=dict(width=2),
            ))

        fig.update_layout(
            title=title,
            xaxis_title=x_column,
            yaxis_title='Value',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
            hovermode='x unified',
        )

        return fig

    def create_distribution_plot(
        self,
        column: str,
        title: str = 'Distribution Plot',
        **kwargs
    ) -> go.Figure:
        """Create distribution plot with histogram and KDE"""
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=self.df[column],
            nbinsx=50,
            name='Histogram',
            marker=dict(color=PLOTLY_COLORS['neon_blue'], opacity=0.7),
        ))

        fig.update_layout(
            title=title,
            xaxis_title=column,
            yaxis_title='Frequency',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
        )

        return fig

    def create_pair_plot_placeholder(self) -> go.Figure:
        """Placeholder for pair plot (full implementation requires seaborn)"""
        fig = go.Figure()
        
        fig.add_annotation(
            text="Pair Plot - Under Development",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color=PLOTLY_COLORS['neon_purple']),
        )

        fig.update_layout(
            title='Pair Plot',
            plot_bgcolor=PLOTLY_COLORS['background'],
            paper_bgcolor=PLOTLY_COLORS['background'],
            font=dict(color=PLOTLY_COLORS['font_color'], size=12),
            template='plotly_dark',
        )

        return fig

    def get_visualization_methods(self) -> Dict[str, callable]:
        """Get all available visualization methods"""
        return {
            'line': self.create_line_chart,
            'bar': self.create_bar_chart,
            'histogram': self.create_histogram,
            'scatter': self.create_scatter_plot,
            'pie': self.create_pie_chart,
            'heatmap': self.create_heatmap,
            'boxplot': self.create_boxplot,
            'area': self.create_area_chart,
            'distribution': self.create_distribution_plot,
            'pair': self.create_pair_plot_placeholder,
        }

    def create_visualization(
        self,
        chart_type: str,
        title: str = '',
        **kwargs
    ) -> go.Figure:
        """
        Create visualization by type
        
        Args:
            chart_type: Type of chart (line, bar, scatter, etc.)
            title: Chart title
            **kwargs: Additional arguments for specific chart type
            
        Returns:
            Plotly Figure object
        """
        methods = self.get_visualization_methods()
        
        if chart_type not in methods:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        method = methods[chart_type]
        return method(title=title or f"{chart_type.title()} Chart", **kwargs)

    def to_html(self, fig: go.Figure, include_plotlyjs: str = 'cdn') -> str:
        """Convert figure to HTML"""
        return fig.to_html(include_plotlyjs=include_plotlyjs, config={'responsive': True})

    def to_image(self, fig: go.Figure, format: str = 'png', width: int = 1200, height: int = 600) -> bytes:
        """
        Convert figure to image (requires kaleido)
        This is a placeholder - requires: pip install kaleido
        """
        try:
            return fig.to_image(format=format, width=width, height=height)
        except Exception as e:
            logger.warning(f"Image export not available: {str(e)}")
            return None
