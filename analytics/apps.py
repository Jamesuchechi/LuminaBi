from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    name = 'analytics'

    def ready(self):
        # Import signals to broadcast analytics events to dashboard hub
        try:
            import analytics.signals  # noqa: F401
        except Exception:
            pass
