"""
URL configuration for the accounts application.
Handles authentication, profile management, and account-related operations.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ====================================================================
    # AUTHENTICATION
    # ====================================================================
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # ====================================================================
    # EMAIL VERIFICATION
    # ====================================================================
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # ====================================================================
    # PROFILE MANAGEMENT
    # ====================================================================
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    
    # ====================================================================
    # PASSWORD MANAGEMENT
    # ====================================================================
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # ====================================================================
    # ORGANIZATION INVITATIONS
    # ====================================================================
    path('invitation/<str:token>/', views.InvitationAcceptView.as_view(), name='accept_invitation'),
]
