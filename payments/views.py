"""
Professional Payment Views
Handles WiFi plan purchases and KCB Buni STK Push integration
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from authentication.decorators import admin_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import PaymentTransaction, STKPushRequest, PaymentCallback
from billing.models import WifiUser, WifiPlan
from .services.payment_processor import payment_processor
from .services.kcb_client import kcb_client, KCBBuniError

import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# PAYMENT PURCHASE ENDPOINTS
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def purchase_wifi_plan(request):
    """
    API endpoint for purchasing WiFi plans with STK Push
    
    Expected payload:
    {
        "phone_number": "254712345678",
        "plan_id": "uuid-here",
        "user_details": {
            "name": "John Doe",
            "email": "john@example.com"  # optional
        }
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        phone_number = data.get('phone_number')
        plan_id = data.get('plan_id')
        user_details = data.get('user_details', {})
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not plan_id:
            return Response({
                'success': False,
                'message': 'Plan ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone number format
        try:
            formatted_phone = kcb_client._format_phone_number(phone_number)
        except KCBBuniError as e:
            return Response({
                'success': False,
                'message': f'Invalid phone number: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get WiFi plan
        try:
            plan = WifiPlan.objects.get(id=plan_id, is_active=True)
        except WifiPlan.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Plan not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create WiFi user
        user, created = WifiUser.objects.get_or_create(
            phone_number=formatted_phone,
            defaults={
                'status': 'pending',
                'created_at': timezone.now()
            }
        )
        
        # Update user details if provided
        if user_details.get('name'):
            user.name = user_details['name']
        if user_details.get('email'):
            user.email = user_details['email']
        user.save()
        
        logger.info(f"Processing WiFi plan purchase: {user.phone_number} -> {plan.name}")
        
        # Process payment with our payment processor
        result = payment_processor.process_wifi_plan_purchase(
            user=user,
            plan=plan,
            phone_number=formatted_phone
        )
        
        if result['success']:
            return Response({
                'success': True,
                'data': {
                    'transaction_id': result['transaction_id'],
                    'checkout_request_id': result.get('checkout_request_id'),
                    'message': result['message'],
                    'plan': {
                        'name': plan.name,
                        'price': float(plan.price),
                        'duration': plan.get_duration_display() if hasattr(plan, 'get_duration_display') else 'N/A'
                    },
                    'user': {
                        'phone_number': user.phone_number,
                        'status': user.status
                    },
                    'next_steps': result.get('next_steps', 'Complete payment on your phone')
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'error_code': result.get('error_code')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in purchase_wifi_plan: {str(e)}")
        return Response({
            'success': False,
            'message': 'System error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_status_api(request, transaction_id):
    """
    API endpoint to check payment status
    """
    try:
        result = payment_processor.query_payment_status(transaction_id)
        
        if result['success']:
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error querying payment status: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error querying payment status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def retry_payment(request, transaction_id):
    """
    API endpoint to retry failed payment
    """
    try:
        result = payment_processor.retry_failed_payment(transaction_id)
        
        if result['success']:
            return Response({
                'success': True,
                'data': {
                    'transaction_id': result['transaction_id'],
                    'checkout_request_id': result.get('checkout_request_id'),
                    'message': result['message']
                }
            })
        else:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error retrying payment: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrying payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# KCB BUNI WEBHOOK ENDPOINTS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def kcb_callback(request):
    """
    KCB Buni payment callback endpoint
    This endpoint receives payment confirmations from KCB Buni
    """
    try:
        # Log the incoming request
        logger.info(f"KCB Buni callback received from {request.META.get('REMOTE_ADDR')}")
        
        if not request.body:
            logger.error("Empty callback body received")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Empty request body'})
        
        try:
            callback_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in callback: {str(e)}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON format'})
        
        logger.info(f"Callback data structure: {json.dumps(callback_data, indent=2)}")
        
        # Process callback with payment processor
        result = payment_processor.handle_payment_callback(callback_data)
        
        if result['success']:
            logger.info(f"Callback processed successfully: {result.get('transaction_id')}")
            return JsonResponse({
                'ResultCode': 0,
                'ResultDesc': 'Callback processed successfully'
            })
        else:
            logger.error(f"Callback processing failed: {result['message']}")
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': result['message']
            })
    
    except Exception as e:
        logger.error(f"Critical error processing KCB callback: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Internal server error'
        })


@csrf_exempt
@require_http_methods(["POST"])
def kcb_timeout(request):
    """
    KCB Buni timeout callback endpoint
    Called when payment times out
    """
    try:
        logger.info("KCB Buni timeout callback received")
        
        if request.body:
            try:
                callback_data = json.loads(request.body.decode('utf-8'))
                logger.info(f"Timeout callback data: {json.dumps(callback_data, indent=2)}")
                
                # Handle timeout logic here if needed
                # For now, just log and acknowledge
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in timeout callback")
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Timeout callback received'
        })
    
    except Exception as e:
        logger.error(f"Error processing timeout callback: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Error processing timeout'
        })


# =============================================================================
# ADMIN VIEWS
# =============================================================================

@admin_required
def payment_dashboard(request):
    """
    Admin dashboard for payment management
    """
    # Recent transactions
    recent_transactions = PaymentTransaction.objects.select_related(
        'user', 'plan'
    ).order_by('-created_at')[:20]
    
    # Payment statistics
    today = timezone.now().date()
    stats = {
        'total_transactions': PaymentTransaction.objects.count(),
        'successful_payments': PaymentTransaction.objects.filter(status='completed').count(),
        'pending_payments': PaymentTransaction.objects.filter(status='processing').count(),
        'failed_payments': PaymentTransaction.objects.filter(status='failed').count(),
        'today_transactions': PaymentTransaction.objects.filter(created_at__date=today).count(),
        'today_revenue': PaymentTransaction.objects.filter(
            created_at__date=today, 
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0,
    }
    
    context = {
        'recent_transactions': recent_transactions,
        'stats': stats
    }
    
    return render(request, 'payments/dashboard.html', context)


@admin_required
def transaction_detail(request, transaction_id):
    """
    Detailed view of a specific transaction
    """
    transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
    
    # Get related STK Push request if exists
    stk_request = getattr(transaction, 'stk_request', None)
    
    # Get all callbacks for this transaction
    callbacks = transaction.callbacks.order_by('-created_at')
    
    context = {
        'transaction': transaction,
        'stk_request': stk_request,
        'callbacks': callbacks
    }
    
    return render(request, 'payments/transaction_detail.html', context)


# =============================================================================
# TEST AND UTILITY ENDPOINTS
# =============================================================================

@admin_required
def test_kcb_connection(request):
    """
    Test KCB Buni API connection
    """
    try:
        test_result = kcb_client.test_connection()
        
        return JsonResponse({
            'success': test_result['success'],
            'message': test_result['message'],
            'environment': test_result['environment'],
            'base_url': test_result['base_url'],
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error testing KCB connection: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Connection test failed: {str(e)}',
            'timestamp': timezone.now().isoformat()
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def available_plans(request):
    """
    Get available WiFi plans for purchase
    """
    try:
        plans = WifiPlan.objects.filter(is_active=True).order_by('price')
        
        plans_data = []
        for plan in plans:
            plan_data = {
                'id': str(plan.id),
                'name': plan.name,
                'price': float(plan.price),
                'currency': 'KES',
                'description': plan.description,
                'plan_type': plan.plan_type,
                'features': []
            }
            
            # Add duration info
            if plan.duration_minutes:
                if plan.duration_minutes < 60:
                    plan_data['duration'] = f"{plan.duration_minutes} minutes"
                elif plan.duration_minutes < 1440:
                    plan_data['duration'] = f"{plan.duration_minutes // 60} hours"
                else:
                    plan_data['duration'] = f"{plan.duration_minutes // 1440} days"
                plan_data['features'].append(f"Duration: {plan_data['duration']}")
            
            # Add data limit info
            if plan.data_limit_mb:
                if plan.data_limit_mb < 1024:
                    plan_data['data_limit'] = f"{plan.data_limit_mb} MB"
                else:
                    plan_data['data_limit'] = f"{plan.data_limit_mb / 1024:.1f} GB"
                plan_data['features'].append(f"Data: {plan_data['data_limit']}")
            
            # Add speed info
            if plan.download_speed_kbps:
                if plan.download_speed_kbps < 1024:
                    speed = f"{plan.download_speed_kbps} Kbps"
                else:
                    speed = f"{plan.download_speed_kbps / 1024:.1f} Mbps"
                plan_data['features'].append(f"Speed: {speed}")
            
            plans_data.append(plan_data)
        
        return Response({
            'success': True,
            'data': {
                'plans': plans_data,
                'count': len(plans_data),
                'environment': settings.KCB_BUNI_ENVIRONMENT
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error fetching available plans'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def payment_status_page(request, transaction_id):
    """
    Customer-facing payment status page
    """
    try:
        transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
        
        context = {
            'transaction': transaction,
            'plan': transaction.plan,
            'user': transaction.user,
            'can_retry': transaction.can_retry,
        }
        
        return render(request, 'payments/status.html', context)
    
    except Exception as e:
        logger.error(f"Error loading payment status page: {str(e)}")
        return render(request, 'payments/error.html', {
            'error_message': 'Transaction not found'
        })