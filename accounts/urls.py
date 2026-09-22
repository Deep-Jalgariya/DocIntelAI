from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('password/change/', views.change_password_view, name='change_password'),
    path('password/forgot/', views.forgot_password_view, name='forgot_password'),
    path('password/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('password/resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('password/reset/', views.reset_password_view, name='reset_password'),
    path('settings/update/', views.update_settings, name='update_settings'),
]

