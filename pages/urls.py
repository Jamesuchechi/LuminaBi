from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.StaticPageView.as_view(template_name='pages/about.html'), name='about'),
    path('faq/', views.StaticPageView.as_view(template_name='pages/faq.html'), name='faq'),
    path('privacy/', views.StaticPageView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', views.StaticPageView.as_view(template_name='pages/terms.html'), name='terms'),
    path('contact/', views.StaticPageView.as_view(template_name='pages/contact.html'), name='contact'),
]
