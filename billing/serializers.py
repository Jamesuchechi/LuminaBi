"""
DRF Serializers for Billing and Subscription models.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    SubscriptionPlan, Team, Subscription, TrialUsage,
    PaymentTransaction, Discount, Invoice
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serialize subscription plans."""
    monthly_price_display = serializers.SerializerMethodField()
    yearly_price_display = serializers.SerializerMethodField()
    months_24_price_display = serializers.SerializerMethodField()
    monthly_equivalent = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'tier', 'name', 'description', 'price_monthly',
            'price_yearly', 'price_24months', 'monthly_price_display',
            'yearly_price_display', 'months_24_price_display',
            'monthly_equivalent', 'max_team_size', 'features',
            'trial_daily_limit', 'trial_duration_days', 'is_active', 'sort_order'
        ]
        read_only_fields = ['id']
    
    def get_monthly_price_display(self, obj):
        return f"${obj.price_monthly / 100:.2f}"
    
    def get_yearly_price_display(self, obj):
        return f"${obj.price_yearly / 100:.2f}"
    
    def get_months_24_price_display(self, obj):
        return f"${obj.price_24months / 100:.2f}"
    
    def get_monthly_equivalent(self, obj):
        return {
            'monthly': obj.get_monthly_equivalent('monthly'),
            'yearly': obj.get_monthly_equivalent('yearly'),
            '24months': obj.get_monthly_equivalent('24months'),
        }


class TeamSerializer(serializers.ModelSerializer):
    """Serialize team data."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'owner', 'owner_username', 'members',
            'member_count', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.member_count


class TrialUsageSerializer(serializers.ModelSerializer):
    """Serialize trial usage tracking."""
    
    class Meta:
        model = TrialUsage
        fields = ['id', 'subscription', 'date', 'count']
        read_only_fields = ['id', 'date']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serialize subscription data."""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    days_remaining = serializers.SerializerMethodField()
    trial_days_remaining = serializers.SerializerMethodField()
    is_trial = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'username', 'team', 'team_name', 'plan',
            'plan_name', 'billing_cycle', 'status', 'start_date',
            'end_date', 'trial_end_date', 'is_active', 'auto_renew',
            'payment_method', 'payment_reference', 'days_remaining',
            'trial_days_remaining', 'is_trial', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_days_remaining(self, obj):
        return obj.days_remaining()
    
    def get_trial_days_remaining(self, obj):
        return obj.trial_days_remaining()
    
    def get_is_trial(self, obj):
        return obj.is_trial()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serialize payment transactions."""
    amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'subscription', 'amount', 'amount_display', 'currency',
            'provider', 'provider_reference', 'status', 'description',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']
    
    def get_amount_display(self, obj):
        return f"{obj.currency} {obj.amount / 100:.2f}"


class DiscountSerializer(serializers.ModelSerializer):
    """Serialize discount codes."""
    
    class Meta:
        model = Discount
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'valid_from', 'valid_until', 'max_uses', 'times_used',
            'applicable_plans', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'times_used']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serialize invoices."""
    amount_due_display = serializers.SerializerMethodField()
    amount_paid_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'subscription', 'invoice_number', 'status',
            'amount_due', 'amount_due_display', 'amount_paid',
            'amount_paid_display', 'issued_date', 'due_date',
            'paid_date', 'description', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_amount_due_display(self, obj):
        return f"${obj.amount_due / 100:.2f}"
    
    def get_amount_paid_display(self, obj):
        return f"${obj.amount_paid / 100:.2f}"


class PricingPageDataSerializer(serializers.Serializer):
    """Serializer for pricing page data."""
    plans = SubscriptionPlanSerializer(many=True, read_only=True)
    user_subscription = SubscriptionSerializer(read_only=True, allow_null=True)
    is_authenticated = serializers.BooleanField(read_only=True)
    current_plan = serializers.CharField(read_only=True, allow_null=True)
