"""
Management command to create default subscription plans.
Usage: python manage.py create_subscription_plans
"""

from django.core.management.base import BaseCommand
from billing.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Creates default subscription plans for the billing system'

    def handle(self, *args, **options):
        plans_data = [
            {
                'tier': 'individual',
                'name': 'Individual',
                'description': 'Perfect for solo users and small projects',
                'price_monthly': 900,  # $9/month in cents
                'price_yearly': 9000,  # $90/year (20% savings)
                'price_24months': 18000,  # $180/24 months (35% savings)
                'max_team_size': 1,
                'features': [
                    'Unlimited datasets',
                    'Unlimited visualizations',
                    '5 uses per day limit',
                    'Basic analytics',
                    'Email support',
                ],
                'trial_daily_limit': 5,
                'trial_duration_days': 14,
                'sort_order': 1,
                'is_active': True,
            },
            {
                'tier': 'team',
                'name': 'Team',
                'description': 'Ideal for small teams and collaborations',
                'price_monthly': 2900,  # $29/month in cents
                'price_yearly': 29000,  # $290/year
                'price_24months': 58000,  # $580/24 months
                'max_team_size': 5,
                'features': [
                    'Everything in Individual',
                    'Team collaboration',
                    'Up to 5 team members',
                    'Advanced analytics',
                    'Unlimited uses',
                    'Priority email support',
                    'Custom branding',
                ],
                'trial_daily_limit': 10,
                'trial_duration_days': 14,
                'sort_order': 2,
                'is_active': True,
            },
            {
                'tier': 'business',
                'name': 'Business',
                'description': 'For growing teams with advanced needs',
                'price_monthly': 9900,  # $99/month in cents
                'price_yearly': 99000,  # $990/year
                'price_24months': 198000,  # $1980/24 months
                'max_team_size': 0,  # Unlimited
                'features': [
                    'Everything in Team',
                    'Unlimited team members',
                    'Advanced scheduling',
                    'Real-time collaboration',
                    'API access',
                    'Webhook support',
                    'Phone support',
                    'SLA guarantee',
                ],
                'trial_daily_limit': 50,
                'trial_duration_days': 14,
                'sort_order': 3,
                'is_active': True,
            },
            {
                'tier': 'enterprise',
                'name': 'Enterprise',
                'description': 'Custom solutions for large organizations',
                'price_monthly': 999900,  # $9,999/month in cents (placeholder)
                'price_yearly': 119988000,  # $1,199,880/year (placeholder)
                'price_24months': 239976000,  # Contact sales (placeholder)
                'max_team_size': 0,  # Unlimited
                'features': [
                    'Everything in Business',
                    'Custom integrations',
                    'Dedicated account manager',
                    'Advanced security features',
                    'White-label solutions',
                    '24/7 phone support',
                    'Custom SLA',
                    'On-premises deployment option',
                ],
                'trial_daily_limit': 0,  # No trial for enterprise
                'trial_duration_days': 0,  # Contact sales
                'sort_order': 4,
                'is_active': True,
            },
        ]

        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                tier=plan_data['tier'],
                defaults=plan_data,
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{status} plan: {plan.name} (${plan.price_monthly/100:.2f}/month)')
            )

        self.stdout.write(self.style.SUCCESS('\nSuccessfully created/updated all subscription plans'))
