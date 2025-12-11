from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Visualization(models.Model):
    CHART_TYPES = [
        ('bar', 'Bar'),
        ('line', 'Line'),
        ('pie', 'Pie'),
        ('scatter', 'Scatter'),
        ('heatmap', 'Heatmap'),
        ('area', 'Area'),
        ('radar', 'Radar'),
        ('bubble', 'Bubble'),
        ('donut', 'Donut'),
        ('treemap', 'Treemap'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visualizations'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    chart_type = models.CharField(max_length=32, choices=CHART_TYPES)
    # JSON configuration for Chart.js / Plotly
    config = models.JSONField(default=dict, blank=True)
    dataset = models.ForeignKey(
        'datasets.Dataset', null=True, blank=True, on_delete=models.SET_NULL, related_name='visualizations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.owner})"
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = "Untitled Visualization"
        super().save(*args, **kwargs)
    
    def generate_config_from_dataset(self):
        """
        Automatically generate JSON configuration from linked dataset.
        Called when user selects a dataset to visualize.
        """
        if not self.dataset:
            logger.warning(f"Cannot generate config for visualization {self.id}: no dataset linked")
            return False
        
        try:
            from .config_generator import ChartConfigGenerator
            import pandas as pd
            import os
            
            # Read the dataset file
            if not os.path.exists(self.dataset.file.path):
                logger.error(f"Dataset file not found: {self.dataset.file.path}")
                return False
            
            # Parse the file based on type
            from datasets.services import FileParser
            df = FileParser.parse_file(self.dataset.file.path, self.dataset.file_type)
            
            # Generate configuration
            generator = ChartConfigGenerator(df, self.dataset.column_names)
            self.config = generator.generate_config(
                chart_type=self.chart_type,
                title=self.title or f"{self.get_chart_type_display()} Chart"
            )
            
            logger.info(f"Successfully generated config for visualization {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error generating config for visualization {self.id}: {str(e)}", exc_info=True)
            return False
    
    def get_suggested_chart_type(self):
        """
        Get the suggested chart type for the linked dataset
        """
        if not self.dataset:
            return self.chart_type
        
        try:
            from .config_generator import ChartConfigGenerator
            from datasets.services import FileParser
            import pandas as pd
            import os
            
            if not os.path.exists(self.dataset.file.path):
                return self.chart_type
            
            df = FileParser.parse_file(self.dataset.file.path, self.dataset.file_type)
            generator = ChartConfigGenerator(df, self.dataset.column_names)
            return generator.suggest_best_chart_type()
        except Exception as e:
            logger.error(f"Error suggesting chart type: {str(e)}")
            return self.chart_type
        
class VisualizationAccessLog(models.Model):
    visualization = models.ForeignKey(
        Visualization, on_delete=models.CASCADE, related_name='access_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-accessed_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} accessed {self.visualization.title} at {self.accessed_at}"
    
class VisualizationTag(models.Model):
    visualization = models.ForeignKey(
        Visualization, on_delete=models.CASCADE, related_name='tags'
    )
    name = models.CharField(max_length=64)

    class Meta:
        unique_together = ('visualization', 'name')

    def __str__(self):
        return f"{self.name} (Visualization: {self.visualization.title})"

class VisualizationComment(models.Model):
    visualization = models.ForeignKey(
        Visualization, on_delete=models.CASCADE, related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.visualization.title}" 
    
class VisualizationFavorite(models.Model):
    visualization = models.ForeignKey(
        Visualization, on_delete=models.CASCADE, related_name='favorites'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    favorited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('visualization', 'user')
        ordering = ['-favorited_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.visualization.title}" 