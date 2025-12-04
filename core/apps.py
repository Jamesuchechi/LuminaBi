from django.apps import AppConfig
import logging

logger = logging.getLogger('scheduler')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """
        Initialize the scheduler when Django starts.
        This method is called when the app is ready.
        """
        # Import here to avoid issues during testing
        from .scheduler import start_scheduler
        
        try:
            start_scheduler()
        except Exception as e:
            logger.warning(f'Failed to start scheduler during app initialization: {e}')

