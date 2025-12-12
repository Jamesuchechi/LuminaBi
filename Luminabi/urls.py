
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from accounts.views import LandingPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='landing'),  # Landing page
    path('accounts/', include('accounts.urls')),  # Accounts
    path('billing/', include('billing.urls')),  # Billing & Subscriptions
    path('core/', include('core.urls')),  # Core application (includes dashboards)
    path('analytics/', include('analytics.urls')),  # Analytics application
    path('datasets/', include('datasets.urls')),  # Datasets application
    path('visualizations/', include('visualizations.urls')),  # Visualizations application
    path('insights/', include('insights.urls')),  # Insights application
    path('pages/', include('pages.urls')),  # Static pages (About, FAQ, Privacy, Terms, Contact)
    path('api/', include('api.urls')),  # REST API
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
