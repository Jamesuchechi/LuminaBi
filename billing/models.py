"""
Billing and Subscription Models for LuminaBI.
Handles pricing tiers, subscriptions, trials, and team management.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import json


class SubscriptionPlan(models.Model):
    """
    Subscription plans with multiple billing cycles.
    """
    PLAN_TIER_CHOICES = [
        ('individual', 'Individual (Personal)'),
        ('team', 'Team (5 Users)'),
        ('business', 'Business (Unlimited)'),
        ('enterprise', 'Enterprise (Custom)'),
    ]
    
    tier = models.CharField(
        max_length=20,
        choices=PLAN_TIER_CHOICES,
        unique=True,
        db_index=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Pricing in cents (USD)
    price_monthly = models.PositiveIntegerField(help_text="Price in cents (USD)")
    price_yearly = models.PositiveIntegerField(help_text="Price in cents (USD)")
    price_24months = models.PositiveIntegerField(help_text="Price in cents (USD)")
    
    # Team size limits
    max_team_size = models.PositiveIntegerField(
        default=1,
        help_text="Max team members. 0 = unlimited"
    )
    
    # Features as JSON
    features = models.JSONField(
        default=dict,
        help_text="Features included in this plan"
    )
    
    # Trial settings per plan
    trial_daily_limit = models.PositiveIntegerField(
        default=5,
        help_text="Max uses per day during trial"
    )
    trial_duration_days = models.PositiveIntegerField(
        default=14,
        help_text="Trial period in days"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'tier']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        indexes = [
            models.Index(fields=['tier']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tier})"
    
    def get_price(self, billing_cycle='monthly'):
        """Get price for a specific billing cycle."""
        if billing_cycle == 'monthly':
            return self.price_monthly
        elif billing_cycle == 'yearly':
            return self.price_yearly
        elif billing_cycle == '24months':
            return self.price_24months
        return self.price_monthly
    
    def get_monthly_equivalent(self, billing_cycle='monthly'):
        """Calculate monthly equivalent price."""
        price = self.get_price(billing_cycle)
        if billing_cycle == 'yearly':
            return price / 12
        elif billing_cycle == '24months':
            return price / 24
        return price


class Team(models.Model):
    """
    Team model for organizing users.
    Used by Team, Business, and Enterprise plans.
    """
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_teams'
    )
    members = models.ManyToManyField(
        User,
        related_name='teams',
        blank=True
    )
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        indexes = [
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.name
    
    def add_member(self, user):
        """Add a member to the team."""
        if self.members.count() >= self.subscription.plan.max_team_size and \
           self.subscription.plan.max_team_size > 0:
            raise ValidationError("Team member limit reached")
        self.members.add(user)
    
    def remove_member(self, user):
        """Remove a member from the team."""
        if user == self.owner:
            raise ValidationError("Cannot remove team owner")
        self.members.remove(user)
    
    @property
    def member_count(self):
        return self.members.count() + 1  # +1 for owner


class Subscription(models.Model):
    """
    Subscription model linking users/teams to plans.
    """
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('24months', '24 Months'),
    ]
    
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    # Owner reference (can be user or team owner)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    
    # Optional team reference
    team = models.OneToOneField(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription'
    )
    
    # Plan and billing
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly'
    )
    
    # Dates
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    
    # Payment tracking
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('paystack', 'Paystack'),
            ('flutterwave', 'Flutterwave'),
            ('stripe', 'Stripe'),
        ]
    )
    payment_reference = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    def is_trial(self):
        """Check if subscription is in trial period."""
        return self.status == 'trial'
    
    def is_expired(self):
        """Check if subscription is expired."""
        if self.end_date and timezone.now() >= self.end_date:
            return True
        return False
    
    def days_remaining(self):
        """Calculate days remaining until expiration."""
        if not self.end_date:
            return None
        days = (self.end_date - timezone.now()).days
        return max(0, days)
    
    def trial_days_remaining(self):
        """Calculate trial days remaining."""
        if not self.trial_end_date:
            return None
        days = (self.trial_end_date - timezone.now()).days
        return max(0, days)
    
    def can_use_feature(self):
        """Check if user can access premium features."""
        # Trial expired
        if self.is_trial() and self.trial_end_date and timezone.now() >= self.trial_end_date:
            return False
        
        # Subscription expired
        if self.is_expired():
            return False
        
        # Trial usage limit reached (check TrialUsage)
        if self.is_trial():
            today_usage = self.trial_usage.filter(
                date=timezone.now().date()
            ).first()
            if today_usage and today_usage.count >= self.plan.trial_daily_limit:
                return False
        
        return self.is_active


class TrialUsage(models.Model):
    """
    Track daily trial usage for free trial users.
    Resets daily.
    """
    subscription = models.OneToOneField(
        Subscription,
        on_delete=models.CASCADE,
        related_name='trial_usage'
    )
    
    date = models.DateField(auto_now_add=True)
    count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Trial Usage"
        verbose_name_plural = "Trial Usages"
        unique_together = ['subscription', 'date']
        indexes = [
            models.Index(fields=['subscription', 'date']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user} - {self.date} ({self.count}/{self.subscription.plan.trial_daily_limit})"
    
    def increment(self):
        """Increment daily usage count."""
        if self.count < self.subscription.plan.trial_daily_limit:
            self.count += 1
            self.save()
            return True
        return False
    
    def is_limit_reached(self):
        """Check if daily limit is reached."""
        return self.count >= self.subscription.plan.trial_daily_limit


class PaymentTransaction(models.Model):
    """
    Track all payment transactions.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    amount = models.PositiveIntegerField(help_text="Amount in cents (USD)")
    currency = models.CharField(max_length=3, default='USD')
    
    provider = models.CharField(
        max_length=50,
        choices=[
            ('paystack', 'Paystack'),
            ('flutterwave', 'Flutterwave'),
            ('stripe', 'Stripe'),
        ]
    )
    
    provider_reference = models.CharField(max_length=200, unique=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription']),
            models.Index(fields=['status']),
            models.Index(fields=['provider']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user} - ${self.amount/100:.2f}"


class Discount(models.Model):
    """
    Discount codes for promotions and referrals.
    Placeholder for future enhancement.
    """
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        default='percentage'
    )
    discount_value = models.PositiveIntegerField(help_text="Percentage (0-100) or cents")
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Limits
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    
    # Restrictions
    applicable_plans = models.ManyToManyField(
        SubscriptionPlan,
        blank=True,
        help_text="Leave empty to apply to all plans"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Discount"
        verbose_name_plural = "Discounts"
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Check if discount code is still valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True


class Invoice(models.Model):
    """
    Invoice records for billing history.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    amount_due = models.PositiveIntegerField(help_text="Amount in cents (USD)")
    amount_paid = models.PositiveIntegerField(default=0)
    
    issued_date = models.DateTimeField()
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)
    
    description = models.TextField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['subscription']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.invoice_number
    
    def is_paid(self):
        return self.status == 'paid'
    
    def is_overdue(self):
        return self.status == 'overdue' and timezone.now() > self.due_date

