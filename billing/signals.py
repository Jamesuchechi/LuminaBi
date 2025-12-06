"""
Signals for Billing app.
Handles automatic subscription creation, trial resets, and expiration.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Subscription, SubscriptionPlan, TrialUsage

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    """
    Create a default trial subscription when a new user registers.
    """
    if created:
        try:
            # Get default plan (Individual tier)
            default_plan = SubscriptionPlan.objects.filter(
                tier='individual',
                is_active=True
            ).first()
            
            if not default_plan:
                logger.warning(f"No default plan found for user {instance.username}")
                return
            
            # Create subscription only if it doesn't exist
            if not hasattr(instance, 'subscription'):
                trial_end = timezone.now() + timedelta(
                    days=default_plan.trial_duration_days
                )
                
                subscription = Subscription.objects.create(
                    user=instance,
                    plan=default_plan,
                    status='trial',
                    trial_end_date=trial_end,
                    is_active=True,
                    auto_renew=False
                )
                
                # Create trial usage tracker
                TrialUsage.objects.create(subscription=subscription)
                
                logger.info(f"Trial subscription created for user {instance.username}")
        
        except Exception as e:
            logger.error(f"Error creating default subscription for {instance.username}: {e}")


@receiver(post_save, sender=TrialUsage)
def reset_daily_trial_usage(sender, instance, created, **kwargs):
    """
    Reset trial usage when a new day starts.
    This would be better as a celery task, but we include it here for completeness.
    """
    if created:
        # Check if there's already a usage record for today
        today = timezone.now().date()
        existing = TrialUsage.objects.filter(
            subscription=instance.subscription,
            date=today
        ).exclude(id=instance.id).count()
        
        if existing > 0:
            # Delete duplicate (race condition)
            instance.delete()
