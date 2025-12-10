from django.apps import AppConfig


class DatasetsConfig(AppConfig):
    name = 'datasets'

    def ready(self):
        # Import signals to enable dataset broadcast events
        try:
            import datasets.signals  # noqa: F401
        except Exception:
            # Fallback silently to avoid startup failure
            pass
