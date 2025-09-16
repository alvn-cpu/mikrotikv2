"""
KCB Buni Payment Webhooks and Callback Handlers
Handles payment confirmations, timeouts, and status updates
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import PaymentTransaction
from billing.models import WifiUser
from .kcb_buni_service import KCBBuniService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def kcb_payment_callback(request):
    """
    Handle KCB Buni payment confirmation callbacks
    This endpoint receives payment status updates from KCB Buni
    """
    try:
        # Parse the callback data
        callback_data = json.loads(request.body)
        
        logger.info(f"KCB Payment Callback received: {callback_data}")
        
        # Extract key information
        checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        merchant_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('MerchantRequestID')
        result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        result_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
        
        if not checkout_request_id:
            logger.error("No CheckoutRequestID in callback data")
            return JsonResponse({'status': 'error', 'message': 'Invalid callback data'}, status=400)
        
        # Find the transaction
        try:
            transaction = PaymentTransaction.objects.get(
                gateway_transaction_id=checkout_request_id
            )
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Transaction not found for CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
        
        # Process the callback based on result code
        if result_code == 0:  # Success
            # Extract payment details from callback
            callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            payment_details = {}
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'Amount':
                    payment_details['amount'] = value
                elif name == 'MpesaReceiptNumber':
                    payment_details['mpesa_receipt'] = value
                elif name == 'TransactionDate':
                    payment_details['transaction_date'] = value
                elif name == 'PhoneNumber':
                    payment_details['phone_number'] = value
            
            # Update transaction as completed
            transaction.status = 'completed'
            transaction.mpesa_receipt_number = payment_details.get('mpesa_receipt')
            transaction.gateway_response = callback_data
            transaction.completed_at = timezone.now()
            transaction.save()
            
            # Activate the user's plan
            activate_user_plan(transaction)
            
            logger.info(f"Payment completed successfully: {transaction.transaction_id}")
            
        else:  # Payment failed or cancelled
            transaction.status = 'failed'
            transaction.gateway_response = callback_data
            transaction.save()
            
            logger.info(f"Payment failed: {transaction.transaction_id} - {result_desc}")
        
        return JsonResponse({'status': 'success', 'message': 'Callback processed'})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback data")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Processing error'}, status=500)


@csrf_exempt
@require_POST
def kcb_payment_timeout(request):
    """
    Handle KCB Buni payment timeout notifications
    Called when payment request times out
    """
    try:
        timeout_data = json.loads(request.body)
        
        logger.info(f"KCB Payment Timeout received: {timeout_data}")
        
        checkout_request_id = timeout_data.get('CheckoutRequestID')
        
        if checkout_request_id:
            try:
                transaction = PaymentTransaction.objects.get(
                    gateway_transaction_id=checkout_request_id
                )
                transaction.status = 'timeout'
                transaction.gateway_response = timeout_data
                transaction.save()
                
                logger.info(f"Payment timeout recorded: {transaction.transaction_id}")
                
            except PaymentTransaction.DoesNotExist:
                logger.error(f"Transaction not found for timeout: {checkout_request_id}")
        
        return JsonResponse({'status': 'success', 'message': 'Timeout processed'})
        
    except Exception as e:
        logger.error(f"Error processing payment timeout: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Processing error'}, status=500)


@csrf_exempt
@require_POST
def kcb_reversal_result(request):
    """
    Handle KCB Buni reversal result notifications
    """
    try:
        reversal_data = json.loads(request.body)
        
        logger.info(f"KCB Reversal Result received: {reversal_data}")
        
        # Process reversal result
        # This would update the original transaction as reversed
        
        return JsonResponse({'status': 'success', 'message': 'Reversal processed'})
        
    except Exception as e:
        logger.error(f"Error processing reversal result: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Processing error'}, status=500)


@csrf_exempt
@require_POST
def kcb_balance_result(request):
    """
    Handle KCB Buni balance inquiry results
    """
    try:
        balance_data = json.loads(request.body)
        
        logger.info(f"KCB Balance Result received: {balance_data}")
        
        # Process balance information
        # This could be stored for monitoring purposes
        
        return JsonResponse({'status': 'success', 'message': 'Balance result processed'})
        
    except Exception as e:
        logger.error(f"Error processing balance result: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Processing error'}, status=500)


def activate_user_plan(transaction):
    """
    Activate the WiFi plan for a user after successful payment
    """
    try:
        wifi_user = transaction.user
        plan = transaction.plan
        
        # Set the plan as current
        wifi_user.current_plan = plan
        wifi_user.status = 'active'
        
        # Calculate expiry based on plan type
        now = timezone.now()
        if plan.plan_type == 'time' and plan.duration_minutes:
            wifi_user.plan_started_at = now
            wifi_user.plan_expires_at = now + timedelta(minutes=plan.duration_minutes)
        elif plan.plan_type == 'data' and plan.data_limit_mb:
            wifi_user.plan_started_at = now
            # For data plans, set a reasonable expiry (e.g., 30 days)
            wifi_user.plan_expires_at = now + timedelta(days=30)
        else:
            # Unlimited plan
            wifi_user.plan_started_at = now
            wifi_user.plan_expires_at = now + timedelta(days=365)  # 1 year
        
        # Reset usage counters
        wifi_user.data_used_mb = 0
        wifi_user.time_used_minutes = 0
        
        wifi_user.save()
        
        # Create user account on MikroTik router
        create_mikrotik_user(wifi_user)
        
        logger.info(f"User plan activated: {wifi_user.phone_number} - {plan.name}")
        
    except Exception as e:
        logger.error(f"Error activating user plan: {str(e)}")


def create_mikrotik_user(wifi_user):
    """
    Create or update user account on MikroTik router
    """
    try:
        from mikrotik_integration.models import RouterConfig
        from payments.kcb_buni_service import get_station_for_user_location
        
        # Get the station for this user
        station = get_station_for_user_location(
            ip_address=wifi_user.ip_address,
            mac_address=wifi_user.mac_address
        )
        
        if not station:
            logger.error(f"No station found for user: {wifi_user.phone_number}")
            return
        
        # Here you would integrate with MikroTik API
        # For now, we'll just log the action
        logger.info(f"MikroTik user creation queued: {wifi_user.phone_number} on {station.name}")
        
        # TODO: Implement actual MikroTik API integration
        # This would:
        # 1. Connect to MikroTik router
        # 2. Create/update hotspot user
        # 3. Set appropriate user profile based on plan
        # 4. Enable the user account
        
    except Exception as e:
        logger.error(f"Error creating MikroTik user: {str(e)}")


@csrf_exempt
def payment_status_check(request, transaction_id):
    """
    Manual payment status check endpoint
    Can be used by frontend to poll payment status
    """
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        
        # If transaction is still processing, try to check status with KCB
        if transaction.status == 'processing' and transaction.gateway_transaction_id:
            try:
                # Get the station for this transaction
                from payments.kcb_buni_service import get_station_for_user_location, KCBBuniService
                
                station = get_station_for_user_location(
                    ip_address=transaction.user.ip_address,
                    mac_address=transaction.user.mac_address
                )
                
                if station:
                    kcb_service = KCBBuniService(station_config=station)
                    status_result = kcb_service.check_payment_status(
                        checkout_request_id=transaction.gateway_transaction_id,
                        merchant_request_id=transaction.gateway_merchant_id
                    )
                    
                    if status_result['success']:
                        if status_result['status'] == '0':  # Success
                            transaction.status = 'completed'
                            transaction.mpesa_receipt_number = status_result.get('transaction_id')
                            transaction.completed_at = timezone.now()
                            transaction.save()
                            
                            # Activate user plan
                            activate_user_plan(transaction)
                            
                        elif status_result['status'] in ['1', '2']:  # Failed or cancelled
                            transaction.status = 'failed'
                            transaction.save()
                
            except Exception as e:
                logger.error(f"Error checking payment status: {str(e)}")
        
        return JsonResponse({
            'transaction_id': transaction.transaction_id,
            'status': transaction.status,
            'amount': float(transaction.amount),
            'plan_name': transaction.plan.name,
            'created_at': transaction.created_at.isoformat(),
            'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
            'mpesa_receipt': transaction.mpesa_receipt_number or ''
        })
        
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_payment_statistics():
    """
    Get payment statistics for monitoring
    """
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_transactions': PaymentTransaction.objects.count(),
        'completed_transactions': PaymentTransaction.objects.filter(status='completed').count(),
        'total_revenue': PaymentTransaction.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        'today_transactions': PaymentTransaction.objects.filter(
            created_at__date=today
        ).count(),
        'today_revenue': PaymentTransaction.objects.filter(
            created_at__date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        'week_transactions': PaymentTransaction.objects.filter(
            created_at__date__gte=week_ago
        ).count(),
        'week_revenue': PaymentTransaction.objects.filter(
            created_at__date__gte=week_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        'month_transactions': PaymentTransaction.objects.filter(
            created_at__date__gte=month_ago
        ).count(),
        'month_revenue': PaymentTransaction.objects.filter(
            created_at__date__gte=month_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return stats