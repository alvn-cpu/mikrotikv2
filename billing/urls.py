from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Captive portal URLs
    path('', views.portal_home, name='portal_home'),
    path('plans/', views.plan_selection, name='plan_selection'),
    path('payment/<uuid:plan_id>/', views.payment_form, name='payment_form'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/status/<str:transaction_id>/', views.payment_status, name='payment_status'),
    
    # User status and management
    path('status/', views.user_status, name='user_status'),
    path('logout/', views.user_logout, name='user_logout'),
    
    # API endpoints
    path('api/plans/', views.api_plans, name='api_plans'),
    path('api/user/status/', views.api_user_status, name='api_user_status'),
]