from django.apps import AppConfig


class InsightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insights'
    verbose_name = 'Data Insights'
    
    def ready(self):
        """Initialize app"""
        try:
            import insights.signals  # noqa
        except ImportError:
            pass
