"""
URL Configuration for Billing app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'billing'

router = DefaultRouter()
router.register(r'plans', views.SubscriptionPlanViewSet, basename='plan')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'transactions', views.PaymentTransactionViewSet, basename='transaction')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')

urlpatterns = [
    # Pricing page
    path('pricing/', views.PricingPageView.as_view(), name='pricing'),
    path('api/pricing/', views.PricingAPIView.as_view(), name='api_pricing'),
    
    # Trial
    path('trial/<str:plan_tier>/start/', views.StartTrialView.as_view(), name='start_trial'),
    
    # Subscription management
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('select-payment/', views.SelectPaymentMethodView.as_view(), name='select_payment_method'),
    path('initiate-payment/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    path('verify-payment/', views.PaymentVerificationView.as_view(), name='verify_payment'),
    path('subscription/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('manage/', views.ManageSubscriptionView.as_view(), name='manage_subscription'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('upgrade/', views.UpgradeSubscriptionView.as_view(), name='upgrade_subscription'),
    
    # Teams
    path('teams/', views.TeamListView.as_view(), name='team_list'),
    path('teams/create/', views.CreateTeamView.as_view(), name='team_create'),
    
    # API routes
    path('api/', include(router.urls)),
] + router.urls
