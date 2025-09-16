from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('signup/', views.custom_signup, name='signup'),
    path('logout/', views.custom_logout, name='logout'),
    path('google-login/', views.google_login, name='google_login'),
    path('check-username/', views.check_username, name='check_username'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
]
