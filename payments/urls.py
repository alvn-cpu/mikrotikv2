from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # =============================================================================
    # CUSTOMER PAYMENT API ENDPOINTS
    # =============================================================================
    
    # WiFi plan purchase endpoint
    path('api/purchase/', views.purchase_wifi_plan, name='purchase_wifi_plan'),
    
    # Available plans
    path('api/plans/', views.available_plans, name='available_plans'),
    
    # Payment status endpoints
    path('api/status/<str:transaction_id>/', views.payment_status_api, name='payment_status_api'),
    path('api/retry/<str:transaction_id>/', views.retry_payment, name='retry_payment'),
    
    # Customer-facing status page
    path('status/<str:transaction_id>/', views.payment_status_page, name='payment_status_page'),
    
    # =============================================================================
    # KCB BUNI WEBHOOK ENDPOINTS
    # =============================================================================
    
    # KCB Buni callbacks (used by KCB servers)
    path('kcb/callback/', views.kcb_callback, name='kcb_callback'),
    path('kcb/timeout/', views.kcb_timeout, name='kcb_timeout'),
    
    # =============================================================================
    # ADMIN MANAGEMENT ENDPOINTS
    # =============================================================================
    
    # Admin dashboard
    path('dashboard/', views.payment_dashboard, name='payment_dashboard'),
    path('transaction/<str:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    
    # Testing endpoint
    path('test-connection/', views.test_kcb_connection, name='test_kcb_connection'),
]
