"""
Payment Service Layer for handling payment gateway integrations.
Supports Paystack, Flutterwave, and Stripe.
"""

import logging
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Base payment service class.
    Provides common functionality for all payment providers.
    """
    
    def __init__(self, provider_name):
        self.provider_name = provider_name
    
    def initiate_payment(self, subscription, amount, reference):
        """
        Initiate payment process.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
    
    def verify_payment(self, reference, provider_reference):
        """
        Verify payment completion.
        Must be implemented by subclasses.
        """
        raise NotImplementedError


class PaystackService(PaymentService):
    """
    Paystack payment provider integration.
    """
    
    API_BASE_URL = 'https://api.paystack.co'
    
    def __init__(self, public_key=None, secret_key=None):
        super().__init__('paystack')
        self.public_key = public_key or ''
        self.secret_key = secret_key or ''
    
    def initiate_payment(self, subscription, amount, reference):
        """
        Initialize Paystack payment.
        
        Returns payment URL and reference.
        """
        # TODO: Implement actual Paystack API call
        # This is a placeholder showing the structure
        
        payload = {
            'amount': int(amount * 100),  # Paystack uses kobo (1/100 of Naira)
            'email': subscription.user.email,
            'reference': reference,
            'metadata': {
                'subscription_id': subscription.id,
                'plan': subscription.plan.tier,
                'user_id': subscription.user.id,
            }
        }
        
        logger.info(f"Paystack payment initialized: {reference}")
        
        return {
            'provider': 'paystack',
            'reference': reference,
            'payment_url': f'{self.API_BASE_URL}/transaction/initialize',
            'data': payload
        }
    
    def verify_payment(self, reference, provider_reference):
        """
        Verify Paystack payment.
        
        Returns success/failure status.
        """
        # TODO: Implement actual Paystack verification
        logger.info(f"Paystack payment verification: {reference}")
        
        return {
            'status': 'pending',  # Should be 'success' or 'failed'
            'reference': reference,
            'provider_reference': provider_reference,
        }
    
    def _verify_webhook_signature(self, body, signature):
        """
        Verify webhook signature from Paystack.
        """
        hash_object = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha512
        )
        computed_signature = hash_object.hexdigest()
        
        return computed_signature == signature


class FlutterwaveService(PaymentService):
    """
    Flutterwave payment provider integration.
    """
    
    API_BASE_URL = 'https://api.flutterwave.com/v3'
    
    def __init__(self, public_key=None, secret_key=None):
        super().__init__('flutterwave')
        self.public_key = public_key or ''
        self.secret_key = secret_key or ''
    
    def initiate_payment(self, subscription, amount, reference):
        """
        Initialize Flutterwave payment.
        
        Returns payment URL and reference.
        """
        # TODO: Implement actual Flutterwave API call
        
        payload = {
            'amount': float(amount),
            'currency': 'USD',
            'tx_ref': reference,
            'redirect_url': '',  # Should be set in settings
            'customer': {
                'email': subscription.user.email,
                'name': subscription.user.get_full_name() or subscription.user.username,
            },
            'customizations': {
                'title': f'LuminaBI - {subscription.plan.name}',
                'description': f'Subscription renewal',
            }
        }
        
        logger.info(f"Flutterwave payment initialized: {reference}")
        
        return {
            'provider': 'flutterwave',
            'reference': reference,
            'payment_url': f'{self.API_BASE_URL}/payments',
            'data': payload
        }
    
    def verify_payment(self, reference, provider_reference):
        """
        Verify Flutterwave payment.
        
        Returns success/failure status.
        """
        # TODO: Implement actual Flutterwave verification
        logger.info(f"Flutterwave payment verification: {reference}")
        
        return {
            'status': 'pending',  # Should be 'success' or 'failed'
            'reference': reference,
            'provider_reference': provider_reference,
        }
    
    def _verify_webhook_signature(self, body, signature):
        """
        Verify webhook signature from Flutterwave.
        """
        hash_object = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256
        )
        computed_signature = hash_object.hexdigest()
        
        return computed_signature == signature


class StripeService(PaymentService):
    """
    Stripe payment provider integration.
    """
    
    API_BASE_URL = 'https://api.stripe.com'
    
    def __init__(self, public_key=None, secret_key=None):
        super().__init__('stripe')
        self.public_key = public_key or ''
        self.secret_key = secret_key or ''
    
    def initiate_payment(self, subscription, amount, reference):
        """
        Initialize Stripe payment.
        
        Returns payment URL and reference.
        """
        # TODO: Implement actual Stripe API call
        
        payload = {
            'amount': int(amount * 100),  # Stripe uses cents
            'currency': 'usd',
            'description': f'{subscription.plan.name} subscription',
            'metadata': {
                'subscription_id': subscription.id,
                'plan': subscription.plan.tier,
                'user_id': subscription.user.id,
            }
        }
        
        logger.info(f"Stripe payment initialized: {reference}")
        
        return {
            'provider': 'stripe',
            'reference': reference,
            'payment_url': f'{self.API_BASE_URL}/v1/payment_intents',
            'data': payload
        }
    
    def verify_payment(self, reference, provider_reference):
        """
        Verify Stripe payment.
        
        Returns success/failure status.
        """
        # TODO: Implement actual Stripe verification
        logger.info(f"Stripe payment verification: {reference}")
        
        return {
            'status': 'pending',  # Should be 'success' or 'failed'
            'reference': reference,
            'provider_reference': provider_reference,
        }
    
    def _verify_webhook_signature(self, body, signature):
        """
        Verify webhook signature from Stripe.
        """
        hash_object = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256
        )
        computed_signature = hash_object.hexdigest()
        
        return computed_signature == signature


class PaymentFactory:
    """
    Factory for creating payment service instances.
    """
    
    SERVICES = {
        'paystack': PaystackService,
        'flutterwave': FlutterwaveService,
        'stripe': StripeService,
    }
    
    @classmethod
    def get_service(cls, provider, **kwargs):
        """
        Get payment service instance for provider.
        """
        service_class = cls.SERVICES.get(provider.lower())
        
        if not service_class:
            raise ValueError(f"Unknown payment provider: {provider}")
        
        return service_class(**kwargs)


# Utility functions for subscription operations

def activate_subscription(subscription, payment_reference, provider):
    """
    Activate subscription after successful payment.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Set subscription status
    subscription.status = 'active'
    subscription.is_active = True
    subscription.payment_method = provider
    subscription.payment_reference = payment_reference
    subscription.start_date = timezone.now()
    
    # Calculate end date based on billing cycle
    cycle_days = {
        'monthly': 30,
        'yearly': 365,
        '24months': 730,
    }
    days = cycle_days.get(subscription.billing_cycle, 30)
    subscription.end_date = timezone.now() + timedelta(days=days)
    
    subscription.save()
    
    logger.info(f"Subscription activated for {subscription.user.username}")


def deactivate_subscription(subscription, reason):
    """
    Deactivate subscription (expiration or cancellation).
    """
    subscription.status = 'expired' if 'expired' in reason.lower() else 'cancelled'
    subscription.is_active = False
    subscription.save()
    
    logger.info(f"Subscription deactivated for {subscription.user.username}: {reason}")


def generate_invoice(subscription, amount, description):
    """
    Generate invoice for subscription payment.
    """
    from .models import Invoice
    from django.utils import timezone
    import random
    import string
    
    # Generate unique invoice number
    random_suffix = ''.join(random.choices(string.digits, k=6))
    invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{random_suffix}"
    
    invoice = Invoice.objects.create(
        subscription=subscription,
        invoice_number=invoice_number,
        amount_due=int(amount * 100),  # Convert to cents
        issued_date=timezone.now(),
        due_date=timezone.now() + timedelta(days=30),
        description=description,
        status='issued'
    )
    
    logger.info(f"Invoice created: {invoice_number}")
    return invoice
