"""
Context processors for LuminaBI core application.
Inject organization context and site-wide settings into all templates.
"""

import logging
from django.core.cache import cache
from .models import Organization, Setting

logger = logging.getLogger(__name__)


def organization_context(request):
    """
    Add organization context to all templates.
    Includes current organization, user's organizations, and permissions.
    """
    context = {
        'current_organization': None,
        'user_organizations': [],
        'is_organization_owner': False,
        'is_organization_member': False,
    }
    
    if not request.user.is_authenticated:
        return context
    
    try:
        # Get user's organizations
        user_organizations = Organization.objects.filter(
            members=request.user
        ).order_by('-created_at')
        
        context['user_organizations'] = user_organizations
        
        # Try to get current organization from session or URL parameter
        org_id = request.session.get('current_organization_id')
        if org_id:
            try:
                current_org = user_organizations.get(id=org_id)
                context['current_organization'] = current_org
                context['is_organization_owner'] = current_org.owner == request.user
                context['is_organization_member'] = True
            except Organization.DoesNotExist:
                request.session.pop('current_organization_id', None)
        
        # If no current org but user has organizations, use the first one
        if not context['current_organization'] and user_organizations.exists():
            first_org = user_organizations.first()
            context['current_organization'] = first_org
            context['is_organization_owner'] = first_org.owner == request.user
            context['is_organization_member'] = True
            
    except Exception as e:
        logger.warning(f'Error loading organization context: {e}')
    
    return context


def settings_context(request):
    """
    Add site-wide settings to all templates.
    Caches settings for performance.
    """
    context = {
        'site_settings': {},
        'site_name': 'LuminaBI',
        'site_description': 'Data Analytics Platform',
    }
    
    try:
        # Try to get settings from cache
        cache_key = 'luminabi_site_settings'
        cached_settings = cache.get(cache_key)
        
        if cached_settings is not None:
            context['site_settings'] = cached_settings
        else:
            # Load settings from database
            settings_dict = {}
            for setting in Setting.objects.filter(site_wide=True):
                settings_dict[setting.key] = setting.value
            
            context['site_settings'] = settings_dict
            
            # Cache for 1 hour
            cache.set(cache_key, settings_dict, 3600)
        
        # Override with specific settings
        if 'site_name' in context['site_settings']:
            context['site_name'] = context['site_settings']['site_name']
        
        if 'site_description' in context['site_settings']:
            context['site_description'] = context['site_settings']['site_description']
            
    except Exception as e:
        logger.warning(f'Error loading settings context: {e}')
    
    return context


def user_context(request):
    """
    Add user-specific context to templates.
    """
    context = {
        'user_role': 'guest',
        'is_staff': False,
        'is_superuser': False,
    }
    
    if request.user.is_authenticated:
        context['is_staff'] = request.user.is_staff
        context['is_superuser'] = request.user.is_superuser
        
        if request.user.is_superuser:
            context['user_role'] = 'admin'
        elif request.user.is_staff:
            context['user_role'] = 'staff'
        else:
            context['user_role'] = 'user'
    
    return context
