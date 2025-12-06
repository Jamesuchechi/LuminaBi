"""
Views for Billing and Subscription management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    SubscriptionPlan, Team, Subscription, TrialUsage,
    PaymentTransaction, Discount, Invoice
)
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, TeamSerializer,
    PaymentTransactionSerializer, DiscountSerializer, InvoiceSerializer,
    PricingPageDataSerializer
)


# ============================================================================
# PRICING PAGE VIEWS
# ============================================================================

class PricingPageView(TemplateView):
    """
    Display pricing page with all subscription tiers.
    """
    template_name = 'billing/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all active plans
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
        context['plans'] = plans
        
        # Get user's current subscription if authenticated
        if self.request.user.is_authenticated:
            try:
                context['user_subscription'] = self.request.user.subscription
                context['current_plan'] = self.request.user.subscription.plan.tier
            except Subscription.DoesNotExist:
                context['user_subscription'] = None
                context['current_plan'] = None
        
        return context


class PricingAPIView(APIView):
    """
    API endpoint for pricing data.
    Returns all plans and user's subscription status.
    """
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
        
        user_subscription = None
        current_plan = None
        
        if request.user.is_authenticated:
            try:
                user_subscription = request.user.subscription
                current_plan = user_subscription.plan.tier
            except Subscription.DoesNotExist:
                pass
        
        data = {
            'plans': SubscriptionPlanSerializer(plans, many=True).data,
            'user_subscription': SubscriptionSerializer(user_subscription).data if user_subscription else None,
            'is_authenticated': request.user.is_authenticated,
            'current_plan': current_plan,
        }
        
        return Response(data)


# ============================================================================
# SUBSCRIPTION MANAGEMENT VIEWS
# ============================================================================

class StartTrialView(LoginRequiredMixin, View):
    """
    Start a free trial for a user.
    """
    login_url = 'accounts:login'
    
    def post(self, request, plan_tier):
        # Check if user already has a subscription
        if hasattr(request.user, 'subscription'):
            return JsonResponse({
                'success': False,
                'message': 'You already have an active subscription'
            }, status=400)
        
        # Get plan
        plan = get_object_or_404(SubscriptionPlan, tier=plan_tier, is_active=True)
        
        # Create trial subscription
        from django.utils import timezone
        from datetime import timedelta
        
        trial_end = timezone.now() + timedelta(days=plan.trial_duration_days)
        
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='trial',
            trial_end_date=trial_end,
            is_active=True,
            auto_renew=False
        )
        
        # Create trial usage tracker
        TrialUsage.objects.create(subscription=subscription)
        
        # Create notification
        from core.views import create_notification
        create_notification(
            user=request.user,
            title='Free Trial Started',
            message=f'Your {plan.name} free trial has started. You have {plan.trial_duration_days} days to explore!',
            notification_type='success'
        )
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': 'Trial started successfully',
                'redirect': reverse_lazy('core:index')
            })
        
        return redirect('core:index')


class SubscribeView(LoginRequiredMixin, View):
    """
    Start subscription for a user.
    Prepares payment gateway initialization.
    """
    login_url = 'accounts:login'
    
    def post(self, request):
        plan_tier = request.POST.get('plan')
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        
        # Validate
        if not plan_tier or billing_cycle not in ['monthly', 'yearly', '24months']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid plan or billing cycle'
            }, status=400)
        
        plan = get_object_or_404(SubscriptionPlan, tier=plan_tier, is_active=True)
        
        # Store in session for payment gateway to use
        request.session['pending_subscription'] = {
            'plan_tier': plan_tier,
            'billing_cycle': billing_cycle,
            'plan_name': plan.name,
            'amount': plan.get_price(billing_cycle),
        }
        
        # Redirect to payment gateway selection
        return redirect('billing:select_payment_method')


class SelectPaymentMethodView(LoginRequiredMixin, TemplateView):
    """
    Allow user to select payment method (Paystack, Flutterwave, Stripe).
    """
    template_name = 'billing/select_payment_method.html'
    login_url = 'accounts:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get pending subscription from session
        pending = self.request.session.get('pending_subscription')
        if not pending:
            context['error'] = 'No subscription selected'
            return context
        
        context['pending_subscription'] = pending
        context['payment_methods'] = [
            {'code': 'paystack', 'name': 'Paystack'},
            {'code': 'flutterwave', 'name': 'Flutterwave'},
            {'code': 'stripe', 'name': 'Stripe'},
        ]
        
        return context


class InitiatePaymentView(LoginRequiredMixin, View):
    """
    Initiate payment with selected provider.
    Placeholder for payment gateway integration.
    """
    login_url = 'accounts:login'
    
    def post(self, request):
        provider = request.POST.get('provider')
        
        pending = request.session.get('pending_subscription')
        if not pending:
            return JsonResponse({
                'success': False,
                'message': 'No subscription selected'
            }, status=400)
        
        if provider == 'paystack':
            return self._initiate_paystack_payment(request, pending)
        elif provider == 'flutterwave':
            return self._initiate_flutterwave_payment(request, pending)
        elif provider == 'stripe':
            return self._initiate_stripe_payment(request, pending)
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid payment provider'
        }, status=400)
    
    def _initiate_paystack_payment(self, request, pending):
        """Placeholder for Paystack payment initialization."""
        # TODO: Implement Paystack integration
        return JsonResponse({
            'success': True,
            'provider': 'paystack',
            'message': 'Paystack integration coming soon',
            'action': 'redirect',
            'url': 'https://paystack.com'  # Placeholder
        })
    
    def _initiate_flutterwave_payment(self, request, pending):
        """Placeholder for Flutterwave payment initialization."""
        # TODO: Implement Flutterwave integration
        return JsonResponse({
            'success': True,
            'provider': 'flutterwave',
            'message': 'Flutterwave integration coming soon',
            'action': 'redirect',
            'url': 'https://flutterwave.com'  # Placeholder
        })
    
    def _initiate_stripe_payment(self, request, pending):
        """Placeholder for Stripe payment initialization."""
        # TODO: Implement Stripe integration
        return JsonResponse({
            'success': True,
            'provider': 'stripe',
            'message': 'Stripe integration coming soon',
            'action': 'redirect',
            'url': 'https://stripe.com'  # Placeholder
        })


class PaymentVerificationView(View):
    """
    Verify payment from provider webhooks.
    Placeholder for payment verification logic.
    """
    
    def post(self, request):
        """
        Handle webhook from payment provider.
        Verify payment and activate subscription.
        """
        # TODO: Implement payment verification
        return JsonResponse({'success': True})


class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    """
    Display user's subscription details.
    """
    model = Subscription
    template_name = 'billing/subscription_detail.html'
    login_url = 'accounts:login'
    
    def get_object(self):
        return self.request.user.subscription


class ManageSubscriptionView(LoginRequiredMixin, TemplateView):
    """
    Allow user to manage their subscription.
    """
    template_name = 'billing/manage_subscription.html'
    login_url = 'accounts:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            subscription = self.request.user.subscription
            context['subscription'] = subscription
            context['invoices'] = subscription.invoices.all()[:10]
            context['transactions'] = subscription.transactions.all()[:10]
        except Subscription.DoesNotExist:
            context['error'] = 'No active subscription'
        
        return context


class CancelSubscriptionView(LoginRequiredMixin, View):
    """
    Cancel user's subscription.
    """
    login_url = 'accounts:login'
    
    def post(self, request):
        try:
            subscription = request.user.subscription
            subscription.status = 'cancelled'
            subscription.is_active = False
            subscription.auto_renew = False
            subscription.save()
            
            # Create notification
            from core.views import create_notification
            create_notification(
                user=request.user,
                title='Subscription Cancelled',
                message=f'Your {subscription.plan.name} subscription has been cancelled.',
                notification_type='info'
            )
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Subscription cancelled successfully'
                })
            
            return redirect('billing:manage_subscription')
        
        except Subscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No active subscription'
            }, status=400)


class UpgradeSubscriptionView(LoginRequiredMixin, View):
    """
    Upgrade to a different plan.
    """
    login_url = 'accounts:login'
    
    def post(self, request):
        new_plan_tier = request.POST.get('plan')
        
        try:
            current_subscription = request.user.subscription
            new_plan = get_object_or_404(SubscriptionPlan, tier=new_plan_tier, is_active=True)
            
            # Update subscription
            current_subscription.plan = new_plan
            current_subscription.status = 'active'
            current_subscription.save()
            
            # Create notification
            from core.views import create_notification
            create_notification(
                user=request.user,
                title='Plan Upgraded',
                message=f'Your subscription has been upgraded to {new_plan.name}!',
                notification_type='success'
            )
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Subscription upgraded successfully'
                })
            
            return redirect('billing:manage_subscription')
        
        except Subscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No active subscription'
            }, status=400)


# ============================================================================
# TEAM MANAGEMENT VIEWS
# ============================================================================

class TeamListView(LoginRequiredMixin, ListView):
    """
    List teams owned or member of by the user.
    """
    model = Team
    template_name = 'billing/team/list.html'
    login_url = 'accounts:login'
    
    def get_queryset(self):
        return Team.objects.filter(owner=self.request.user) | \
               Team.objects.filter(members=self.request.user)


class CreateTeamView(LoginRequiredMixin, CreateView):
    """
    Create a new team.
    """
    model = Team
    template_name = 'billing/team/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('billing:team_list')
    login_url = 'accounts:login'
    
    def form_valid(self, form):
        # Check if user has a subscription
        try:
            subscription = self.request.user.subscription
            form.instance.owner = self.request.user
            return super().form_valid(form)
        except Subscription.DoesNotExist:
            form.add_error(None, 'You must have an active subscription to create a team')
            return self.form_invalid(form)


# ============================================================================
# API VIEWSETS
# ============================================================================

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for subscription plans.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's subscription."""
        try:
            subscription = request.user.subscription
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'detail': 'No active subscription'},
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for viewing payment transactions.
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            subscription__user=self.request.user
        )


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for viewing invoices.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Invoice.objects.filter(subscription__user=self.request.user)

