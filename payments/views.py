from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from .models import PaymentTransaction, STKPushRequest, PaymentCallback
from billing.models import WifiUser, WifiPlan
from mikrotik_integration.services import create_mikrotik_user
import json
import logging
import requests
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def kcb_buni_callback(request):
    """Handle KCB Buni payment callbacks"""
    try:
        callback_data = json.loads(request.body)
        logger.info(f"KCB Buni callback received: {callback_data}")
        
        # Extract transaction ID from callback
        transaction_id = callback_data.get('transaction_id') or callback_data.get('TransactionID')
        
        if not transaction_id:
            logger.error("No transaction ID in callback")
            return JsonResponse({'status': 'error', 'message': 'No transaction ID'}, status=400)
        
        # Find the transaction
        try:
            transaction = PaymentTransaction.objects.get(external_transaction_id=transaction_id)
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Transaction not found: {transaction_id}")
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
        
        # Store callback data
        PaymentCallback.objects.create(
            transaction=transaction,
            callback_type='kcb_buni_callback',
            callback_data=callback_data
        )
        
        # Process the callback
        result_code = callback_data.get('result_code') or callback_data.get('ResultCode')
        if result_code == '0' or result_code == 0:  # Success
            transaction.status = 'completed'
            transaction.completed_at = timezone.now()
            transaction.provider_response = callback_data
            transaction.save()
            
            # Activate the user's plan
            activate_user_plan(transaction)
            
            logger.info(f"Payment completed for transaction: {transaction.transaction_id}")
        else:
            transaction.status = 'failed'
            transaction.failure_reason = callback_data.get('result_desc', 'Payment failed')
            transaction.provider_response = callback_data
            transaction.save()
            
            logger.warning(f"Payment failed for transaction: {transaction.transaction_id}")
        
        return JsonResponse({'status': 'success', 'message': 'Callback processed'})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stk_push_callback(request):
    """Handle STK Push callbacks"""
    try:
        callback_data = json.loads(request.body)
        logger.info(f"STK Push callback received: {callback_data}")
        
        # Extract checkout request ID
        checkout_request_id = callback_data.get('CheckoutRequestID')
        
        if not checkout_request_id:
            logger.error("No checkout request ID in callback")
            return JsonResponse({'status': 'error', 'message': 'No checkout request ID'}, status=400)
        
        # Find the STK push request
        try:
            stk_request = STKPushRequest.objects.get(checkout_request_id=checkout_request_id)
        except STKPushRequest.DoesNotExist:
            logger.error(f"STK Push request not found: {checkout_request_id}")
            return JsonResponse({'status': 'error', 'message': 'STK Push request not found'}, status=404)
        
        # Update STK push request
        stk_request.callback_response = callback_data
        stk_request.result_code = callback_data.get('ResultCode', '')
        stk_request.result_desc = callback_data.get('ResultDesc', '')
        
        if stk_request.result_code == '0':  # Success
            stk_request.status = 'accepted'
            stk_request.transaction.status = 'completed'
            stk_request.transaction.completed_at = timezone.now()
            stk_request.transaction.save()
            
            # Activate the user's plan
            activate_user_plan(stk_request.transaction)
            
            logger.info(f"STK Push payment completed: {checkout_request_id}")
        else:
            stk_request.status = 'cancelled' if stk_request.result_code == '1032' else 'failed'
            stk_request.transaction.status = 'failed'
            stk_request.transaction.failure_reason = stk_request.result_desc
            stk_request.transaction.save()
            
            logger.warning(f"STK Push payment failed: {checkout_request_id}")
        
        stk_request.save()
        
        return JsonResponse({'status': 'success', 'message': 'Callback processed'})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in STK Push callback")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing STK Push callback: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Internal error'}, status=500)


def payment_status(request, transaction_id):
    """Display payment status page"""
    transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
    
    context = {
        'transaction': transaction,
        'plan': transaction.plan,
        'user': transaction.user,
    }
    
    return render(request, 'payments/payment_status.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_initiate_payment(request):
    """API endpoint to initiate payment"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        phone_number = data.get('phone_number')
        plan_id = data.get('plan_id')
        
        if not phone_number or not plan_id:
            return JsonResponse({'error': 'Phone number and plan ID required'}, status=400)
        
        # Get plan and create/get user
        plan = get_object_or_404(WifiPlan, id=plan_id, is_active=True)
        user, created = WifiUser.objects.get_or_create(
            phone_number=phone_number,
            defaults={'status': 'pending'}
        )
        
        # Create payment transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            phone_number=phone_number,
            payment_method='kcb_buni',
            status='pending'
        )
        
        # Here we would call the actual KCB Buni API
        # For now, we'll simulate the process
        transaction.status = 'processing'
        transaction.external_transaction_id = f"KCB{transaction.transaction_id}"
        transaction.save()
        
        return JsonResponse({
            'status': 'success',
            'transaction_id': transaction.transaction_id,
            'amount': float(transaction.amount),
            'message': 'Payment initiated. Please check your phone for STK Push.'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        return JsonResponse({'error': 'Internal error'}, status=500)


def api_payment_status(request, transaction_id):
    """API endpoint to check payment status"""
    try:
        transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
        
        return JsonResponse({
            'transaction_id': transaction.transaction_id,
            'status': transaction.status,
            'amount': float(transaction.amount),
            'phone_number': transaction.phone_number,
            'plan': {
                'name': transaction.plan.name,
                'type': transaction.plan.plan_type,
                'duration_minutes': transaction.plan.duration_minutes,
                'data_limit_mb': transaction.plan.data_limit_mb,
            },
            'created_at': transaction.created_at.isoformat(),
            'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
            'failure_reason': transaction.failure_reason if transaction.status == 'failed' else None,
        })
    
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return JsonResponse({'error': 'Internal error'}, status=500)


# Utility functions
def activate_user_plan(transaction):
    """Activate a user's plan after successful payment"""
    try:
        user = transaction.user
        plan = transaction.plan
        
        # Update user status
        user.current_plan = plan
        user.status = 'active'
        user.plan_started_at = timezone.now()
        
        # Set expiration based on plan type
        if plan.plan_type == 'time' and plan.duration_minutes:
            user.plan_expires_at = timezone.now() + timedelta(minutes=plan.duration_minutes)
        elif plan.plan_type == 'data' and plan.data_limit_mb:
            # Data plans don't expire by time, but by usage
            user.plan_expires_at = timezone.now() + timedelta(days=30)  # 30-day validity
        else:
            # Unlimited or other types - set to 24 hours by default
            user.plan_expires_at = timezone.now() + timedelta(hours=24)
        
        user.save()
        
        logger.info(f"User plan activated: {user.phone_number} - {plan.name}")
        
        # Create the user in MikroTik
        try:
            create_mikrotik_user(user)
            logger.info(f"MikroTik user created for {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to create MikroTik user for {user.phone_number}: {str(e)}")
            # Don't fail the entire activation if MikroTik creation fails
        
        return True
    except Exception as e:
        logger.error(f"Error activating user plan: {str(e)}")
        return False


def initiate_kcb_buni_payment(phone_number, amount, transaction_id):
    """Initiate KCB Buni payment (placeholder function)"""
    # This is a placeholder function for KCB Buni API integration
    # You would implement the actual API calls here
    
    api_url = settings.KCB_BUNI_BASE_URL + '/api/v1/payments/initiate'
    headers = {
        'Authorization': f'Bearer {settings.KCB_BUNI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'phone_number': phone_number,
        'amount': str(amount),
        'transaction_id': transaction_id,
        'callback_url': request.build_absolute_uri('/payments/callback/kcb-buni/'),
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"KCB Buni API error: {str(e)}")
        return None
