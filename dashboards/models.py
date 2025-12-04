from django.db import models
from django.conf import settings


class Dashboard(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # layout stores grid/widget layout, widget references, etc.
    layout = models.JSONField(default=dict, blank=True)
    visualizations = models.ManyToManyField(
        'visualizations.Visualization', blank=True, related_name='dashboards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.owner})"
    def scheduled_report_enabled(self):
        """Check if scheduled reports are enabled for this dashboard."""
        return self.settings.get('scheduled_report_enabled', False)
    def get_scheduled_report_frequency(self):
        """Get the frequency of scheduled reports."""
        return self.settings.get('scheduled_report_frequency', 'daily')
    def get_scheduled_report_recipients(self):
        """Get the list of recipients for scheduled reports."""
        return self.settings.get('scheduled_report_recipients', [])
