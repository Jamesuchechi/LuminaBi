"""
Signals for insights app
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from datasets.models import Dataset
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Dataset)
def notify_dataset_ready_for_insights(sender, instance, created, **kwargs):
    """
    Notify when a dataset is ready for insights analysis
    """
    if created:
        logger.info(f"Dataset {instance.name} created - ready for insights generation")
