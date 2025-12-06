"""
Django admin configuration for Billing app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SubscriptionPlan, Team, Subscription, TrialUsage,
    PaymentTransaction, Discount, Invoice
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price_monthly_display', 'max_team_size', 'is_active', 'created_at']
    list_filter = ['tier', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('tier', 'name', 'description', 'sort_order')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_yearly', 'price_24months')
        }),
        ('Configuration', {
            'fields': ('max_team_size', 'trial_daily_limit', 'trial_duration_days', 'features')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_monthly_display(self, obj):
        return f"${obj.price_monthly / 100:.2f}"
    price_monthly_display.short_description = 'Monthly Price'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'member_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'member_count']
    filter_horizontal = ['members']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'owner', 'description')
        }),
        ('Members', {
            'fields': ('members', 'member_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = 'Total Members'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_name', 'status_badge', 'billing_cycle', 'days_remaining_display', 'created_at']
    list_filter = ['status', 'plan__tier', 'billing_cycle', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'plan__name']
    readonly_fields = ['created_at', 'updated_at', 'start_date', 'days_remaining_display', 'trial_days_remaining_display']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'team', 'plan', 'billing_cycle')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end_date')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'auto_renew')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_reference'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('days_remaining_display', 'trial_days_remaining_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = 'Plan'
    
    def status_badge(self, obj):
        colors = {
            'trial': '#FFA500',
            'active': '#28a745',
            'cancelled': '#dc3545',
            'expired': '#6c757d',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining()
        if days is None:
            return 'N/A'
        return f'{days} days'
    days_remaining_display.short_description = 'Days Remaining'
    
    def trial_days_remaining_display(self, obj):
        days = obj.trial_days_remaining()
        if days is None:
            return 'N/A'
        return f'{days} days'
    trial_days_remaining_display.short_description = 'Trial Days Remaining'


@admin.register(TrialUsage)
class TrialUsageAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'date', 'usage_progress', 'is_limit_reached']
    list_filter = ['date', 'subscription__user']
    search_fields = ['subscription__user__username']
    readonly_fields = ['date', 'usage_progress']
    
    def usage_progress(self, obj):
        limit = obj.subscription.plan.trial_daily_limit
        percentage = int((obj.count / limit) * 100) if limit > 0 else 0
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:5px; overflow:hidden;"><div style="width:{}%; background-color:#007bff; height:20px;"></div></div> {}/{}',
            percentage,
            obj.count,
            limit
        )
    usage_progress.short_description = 'Usage'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount_display', 'provider', 'status_badge', 'created_at']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['subscription__user__username', 'provider_reference']
    readonly_fields = ['created_at', 'completed_at', 'amount_display']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('subscription', 'amount', 'amount_display', 'currency')
        }),
        ('Provider', {
            'fields': ('provider', 'provider_reference', 'status')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f"{obj.currency} {obj.amount / 100:.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#6c757d',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'validity_badge', 'times_used', 'is_active']
    list_filter = ['discount_type', 'is_active', 'valid_from']
    search_fields = ['code', 'description']
    filter_horizontal = ['applicable_plans']
    readonly_fields = ['times_used']
    
    fieldsets = (
        ('Code', {
            'fields': ('code', 'description')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Limits', {
            'fields': ('max_uses', 'times_used')
        }),
        ('Plans', {
            'fields': ('applicable_plans',),
            'description': 'Leave empty to apply to all plans'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        return f"${obj.discount_value / 100:.2f}"
    discount_display.short_description = 'Discount'
    
    def validity_badge(self, obj):
        if obj.is_valid():
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Valid</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Invalid</span>'
        )
    validity_badge.short_description = 'Validity'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'amount_due_display', 'status_badge', 'issued_date']
    list_filter = ['status', 'issued_date', 'due_date']
    search_fields = ['invoice_number', 'subscription__user__username']
    readonly_fields = ['created_at', 'updated_at', 'amount_due_display', 'amount_paid_display']
    
    fieldsets = (
        ('Invoice', {
            'fields': ('invoice_number', 'subscription', 'status')
        }),
        ('Amounts', {
            'fields': ('amount_due', 'amount_due_display', 'amount_paid', 'amount_paid_display')
        }),
        ('Dates', {
            'fields': ('issued_date', 'due_date', 'paid_date')
        }),
        ('Description', {
            'fields': ('description', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_due_display(self, obj):
        return f"${obj.amount_due / 100:.2f}"
    amount_due_display.short_description = 'Amount Due'
    
    def amount_paid_display(self, obj):
        return f"${obj.amount_paid / 100:.2f}"
    amount_paid_display.short_description = 'Amount Paid'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'issued': '#FFA500',
            'paid': '#28a745',
            'overdue': '#dc3545',
            'cancelled': '#999',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

