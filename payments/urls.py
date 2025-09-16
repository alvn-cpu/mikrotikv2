from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing URLs
    path('callback/kcb-buni/', views.kcb_buni_callback, name='kcb_buni_callback'),
    path('callback/stk-push/', views.stk_push_callback, name='stk_push_callback'),
    
    # Payment status check
    path('status/<str:transaction_id>/', views.payment_status, name='payment_status'),
    
    # API endpoints
    path('api/initiate-payment/', views.api_initiate_payment, name='api_initiate_payment'),
    path('api/check-status/<str:transaction_id>/', views.api_payment_status, name='api_payment_status'),
]