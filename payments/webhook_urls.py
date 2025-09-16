"""
URL patterns for KCB Buni payment webhooks
"""

from django.urls import path
from . import kcb_webhooks

app_name = 'payments'

urlpatterns = [
    # KCB Buni webhook endpoints
    path('kcb/callback/', kcb_webhooks.kcb_payment_callback, name='kcb_payment_callback'),
    path('kcb/timeout/', kcb_webhooks.kcb_payment_timeout, name='kcb_payment_timeout'),
    path('kcb/reversal/result/', kcb_webhooks.kcb_reversal_result, name='kcb_reversal_result'),
    path('kcb/reversal/timeout/', kcb_webhooks.kcb_payment_timeout, name='kcb_reversal_timeout'),
    path('kcb/balance/result/', kcb_webhooks.kcb_balance_result, name='kcb_balance_result'),
    path('kcb/balance/timeout/', kcb_webhooks.kcb_payment_timeout, name='kcb_balance_timeout'),
    
    # Payment status check endpoint
    path('status/<str:transaction_id>/', kcb_webhooks.payment_status_check, name='payment_status_check'),
]