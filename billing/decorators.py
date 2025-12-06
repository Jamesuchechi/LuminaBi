"""
Decorators for subscription access control.
Use these to protect views and API endpoints.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone


def require_subscription(allowed_plans=None):
    """
    Decorator to require user to have active subscription.
    
    Usage:
        @require_subscription(allowed_plans=['team', 'business', 'enterprise'])
        def my_view(request):
            ...
    
    Args:
        allowed_plans: List of plan tiers that can access. None = any plan.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('accounts:login'))
            
            try:
                subscription = request.user.subscription
            except:
                messages.error(request, 'You must have an active subscription.')
                return redirect(reverse('billing:pricing'))
            
            # Check if subscription is active
            if not subscription.is_active or subscription.is_expired():
                messages.error(request, 'Your subscription has expired.')
                return redirect(reverse('billing:pricing'))
            
            # Check allowed plans
            if allowed_plans and subscription.plan.tier not in allowed_plans:
                messages.error(request, 'Your plan does not have access to this feature.')
                return redirect(reverse('billing:pricing'))
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_trial_available(view_func):
    """
    Decorator to require trial usage to be available.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:login'))
        
        try:
            subscription = request.user.subscription
            
            if subscription.is_trial():
                # Check daily limit
                today_usage = subscription.trial_usage.filter(
                    date__date=timezone.now().date()
                ).first()
                
                if today_usage and today_usage.is_limit_reached():
                    messages.warning(
                        request,
                        f'You have reached your daily trial limit ({subscription.plan.trial_daily_limit} uses/day). '
                        'Please upgrade to continue.'
                    )
                    return redirect(reverse('billing:pricing'))
            
            return view_func(request, *args, **kwargs)
        
        except:
            return redirect(reverse('billing:pricing'))
    
    return wrapper


def trial_usage_tracked(view_func):
    """
    Decorator to automatically track trial usage.
    Increments usage counter and redirects if limit reached.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                subscription = request.user.subscription
                
                if subscription.is_trial():
                    # Get or create today's usage
                    from django.utils import timezone
                    from .models import TrialUsage
                    
                    today = timezone.now().date()
                    usage, created = TrialUsage.objects.get_or_create(
                        subscription=subscription,
                        date=today
                    )
                    
                    # Check if limit reached
                    if usage.is_limit_reached():
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'error': 'Trial daily limit reached',
                                'limit': subscription.plan.trial_daily_limit
                            }, status=429)
                        
                        messages.warning(
                            request,
                            f'You have reached your daily trial limit ({subscription.plan.trial_daily_limit} uses/day).'
                        )
                        return redirect(reverse('billing:pricing'))
                    
                    # Increment usage
                    usage.increment()
            
            except Exception as e:
                # If there's any error with subscription, allow access
                pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def api_require_subscription(allowed_plans=None):
    """
    Decorator for API views to require subscription.
    Returns JSON error responses instead of redirects.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required'
                }, status=401)
            
            try:
                subscription = request.user.subscription
            except:
                return JsonResponse({
                    'error': 'Active subscription required'
                }, status=403)
            
            # Check if subscription is active
            if not subscription.is_active or subscription.is_expired():
                return JsonResponse({
                    'error': 'Subscription expired',
                    'redirect': reverse('billing:pricing')
                }, status=403)
            
            # Check allowed plans
            if allowed_plans and subscription.plan.tier not in allowed_plans:
                return JsonResponse({
                    'error': 'Your plan does not have access to this feature',
                    'redirect': reverse('billing:pricing')
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_trial_usage_tracked(view_func):
    """
    API version of trial_usage_tracked.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                subscription = request.user.subscription
                
                if subscription.is_trial():
                    from django.utils import timezone
                    from .models import TrialUsage
                    
                    today = timezone.now().date()
                    usage, created = TrialUsage.objects.get_or_create(
                        subscription=subscription,
                        date=today
                    )
                    
                    if usage.is_limit_reached():
                        return JsonResponse({
                            'error': 'Trial daily limit reached',
                            'limit': subscription.plan.trial_daily_limit
                        }, status=429)
                    
                    usage.increment()
            
            except Exception as e:
                pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
