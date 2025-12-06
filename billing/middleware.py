"""
Middleware for subscription access control.
Redirects users to pricing page if their subscription is expired or trial limit reached.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SubscriptionAccessMiddleware:
    """
    Middleware to check if user has access to premium features.
    """
    
    # URLs that don't require subscription
    EXEMPT_URLS = [
        '/accounts/',
        '/auth/',
        '/api/auth/',
        '/billing/pricing',
        '/billing/trial/',
        '/billing/subscribe/',
        '/billing/api/pricing/',
        '/admin/',
        '/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if path is exempt
            if not self._is_exempt(request.path):
                # Check subscription status
                if not self._has_access(request.user):
                    messages.warning(
                        request,
                        'Your subscription has expired or trial limit reached. Please upgrade to continue.'
                    )
                    return redirect('billing:pricing')
        
        response = self.get_response(request)
        return response
    
    def _is_exempt(self, path):
        """Check if path is exempt from subscription checks."""
        for exempt_path in self.EXEMPT_URLS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _has_access(self, user):
        """Check if user has access to premium features."""
        # Superusers/admins have unrestricted access
        if user.is_superuser or user.is_staff:
            return True
        
        try:
            subscription = user.subscription
            
            # Check if subscription is active and not expired
            if not subscription.is_active:
                return False
            
            if subscription.is_expired():
                return False
            
            # Check trial limits
            if subscription.is_trial():
                if subscription.trial_end_date:
                    from django.utils import timezone
                    if timezone.now() >= subscription.trial_end_date:
                        return False
                
                # Check daily usage limit
                try:
                    today_usage = subscription.trial_usage.filter(
                        date=timezone.now().date()
                    ).first()
                    if today_usage and today_usage.is_limit_reached():
                        return False
                except:
                    pass
            
            return True
        
        except AttributeError:
            # User doesn't have a subscription yet
            return False
