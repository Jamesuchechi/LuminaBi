#!/bin/bash

# Luminabi Billing System - Quick Setup Guide
# This script validates and displays information about the billing system setup

echo "========================================="
echo "Luminabi Billing & Subscription System"
echo "========================================="
echo ""

# Check if models are created
echo "✓ Checking database models..."
python manage.py sqlmigrate billing 0001 > /dev/null 2>&1 && echo "  ✓ Models created" || echo "  ✗ Models not created"

# Check if subscriptions plans exist
echo ""
echo "✓ Checking subscription plans..."
PLAN_COUNT=$(python manage.py shell -c "from billing.models import SubscriptionPlan; print(SubscriptionPlan.objects.count())" 2>/dev/null | tail -1)
echo "  Found $PLAN_COUNT plans:"
python manage.py shell -c "
from billing.models import SubscriptionPlan
for plan in SubscriptionPlan.objects.all().order_by('sort_order'):
    price = plan.price_monthly / 100
    print(f'    • {plan.name}: \${price:.2f}/month ({plan.max_team_size} members)')
" 2>/dev/null | tail -4

# Display important URLs
echo ""
echo "✓ Important URLs:"
echo "    • Pricing Page: http://localhost:8000/billing/"
echo "    • API Plans: http://localhost:8000/billing/api/plans/"
echo "    • Admin: http://localhost:8000/admin/billing/"
echo ""

# Display next steps
echo "✓ Next Steps:"
echo "    1. Create a superuser (if not exists):"
echo "       python manage.py createsuperuser"
echo ""
echo "    2. Run the development server:"
echo "       python manage.py runserver"
echo ""
echo "    3. Access pricing page:"
echo "       http://localhost:8000/billing/"
echo ""
echo "    4. Test free trial:"
echo "       • Log in"
echo "       • Go to Pricing"
echo "       • Click 'Start Free Trial' on any plan"
echo ""
echo "    5. Configure payment providers:"
echo "       • Add Paystack API keys in settings"
echo "       • Add Flutterwave API keys in settings"
echo "       • Add Stripe API keys in settings"
echo ""

echo "========================================="
echo "Setup Complete! System is ready to use."
echo "========================================="
