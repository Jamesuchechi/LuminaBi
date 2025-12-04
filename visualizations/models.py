from django.db import models
from django.conf import settings


class Visualization(models.Model):
    CHART_TYPES = [
        ('bar', 'Bar'),
        ('line', 'Line'),
        ('pie', 'Pie'),
        ('scatter', 'Scatter'),
        ('heatmap', 'Heatmap'),
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
from django.db import models

# Create your models here.
