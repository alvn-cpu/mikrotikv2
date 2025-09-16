from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from .models import WifiPlan, WifiUser, UserSession
from payments.models import PaymentTransaction
import json
import uuid
import re


def portal_home(request):
    """Simple WiFi captive portal - redirect to plans"""
    mac_address = request.GET.get('mac', '')
    ip_address = request.META.get('REMOTE_ADDR', '')
    
    # Redirect directly to plans page with parameters
    return redirect(f'/plans/?mac={mac_address}&ip={ip_address}')


def plan_selection(request):
    """Display available WiFi plans"""
    plans = WifiPlan.objects.filter(is_active=True).order_by('price')
    
    # Group plans by type
    time_plans = plans.filter(plan_type='time')
    data_plans = plans.filter(plan_type='data')
    unlimited_plans = plans.filter(plan_type='unlimited')
    
    context = {
        'time_plans': time_plans,
        'data_plans': data_plans,
        'unlimited_plans': unlimited_plans,
        'mac_address': request.GET.get('mac', ''),
        'ip_address': request.META.get('REMOTE_ADDR', ''),
    }
    
    return render(request, 'billing/plan_selection.html', context)


def payment_form(request, plan_id):
    """Payment form for selected plan"""
    plan = get_object_or_404(WifiPlan, id=plan_id, is_active=True)
    mac_address = request.GET.get('mac', '')
    ip_address = request.META.get('REMOTE_ADDR', '')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate phone number (Kenyan format)
        if not validate_phone_number(phone_number):
            messages.error(request, 'Please enter a valid phone number (e.g., 254701234567 or 0701234567)')
        else:
            # Normalize phone number
            phone_number = normalize_phone_number(phone_number)
            
            # Create or get WiFi user
            wifi_user, created = WifiUser.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'mac_address': mac_address,
                    'ip_address': ip_address,
                    'status': 'pending'
                }
            )
            
            # Update user info if not created
            if not created:
                wifi_user.mac_address = mac_address
                wifi_user.ip_address = ip_address
                wifi_user.save()
            
            # Redirect to payment processing
            return redirect(f'/payment/process/?plan_id={plan_id}&user_id={wifi_user.id}')
    
    context = {
        'plan': plan,
        'mac_address': mac_address,
        'ip_address': ip_address,
    }
    
    return render(request, 'billing/payment_form.html', context)


def process_payment(request):
    """Process payment initiation with station-specific KCB credentials"""
    plan_id = request.GET.get('plan_id')
    user_id = request.GET.get('user_id')
    
    if not plan_id or not user_id:
        messages.error(request, 'Invalid payment request')
        return redirect('billing:plan_selection')
    
    plan = get_object_or_404(WifiPlan, id=plan_id)
    wifi_user = get_object_or_404(WifiUser, id=user_id)
    
    # Determine which station the user is connecting from
    try:
        from payments.kcb_buni_service import get_station_for_user_location
        station = get_station_for_user_location(
            ip_address=wifi_user.ip_address,
            mac_address=wifi_user.mac_address
        )
        
        if not station or not station.enable_payments:
            messages.error(request, 'Payment not available for this location')
            return redirect('billing:plan_selection')
            
    except Exception as e:
        messages.error(request, 'Unable to determine payment configuration')
        return redirect('billing:plan_selection')
    
    # Create payment transaction
    transaction = PaymentTransaction.objects.create(
        user=wifi_user,
        plan=plan,
        amount=plan.price,
        phone_number=wifi_user.phone_number,
        payment_method='kcb_buni',
        status='pending'
    )
    
    # Initiate KCB Buni payment with station-specific credentials
    try:
        from payments.kcb_buni_service import KCBBuniService
        
        # Initialize KCB service with station credentials
        kcb_service = KCBBuniService(station_config=station)
        
        # Initiate STK Push
        payment_result = kcb_service.initiate_stk_push(
            phone_number=wifi_user.phone_number,
            amount=float(plan.price),
            plan_name=plan.name,
            reference=transaction.transaction_id
        )
        
        if payment_result['success']:
            # Update transaction with payment gateway response
            transaction.gateway_transaction_id = payment_result.get('checkout_request_id')
            transaction.gateway_merchant_id = payment_result.get('merchant_request_id')
            transaction.gateway_response = payment_result.get('raw_response', {})
            transaction.status = 'processing'
            transaction.save()
            
            messages.success(request, 'Payment request sent! Please check your phone for M-Pesa prompt.')
        else:
            transaction.status = 'failed'
            transaction.gateway_response = {'error': payment_result['message']}
            transaction.save()
            
            messages.error(request, f'Payment initiation failed: {payment_result["message"]}')
            
    except ImportError:
        # KCB service not available - use fallback
        transaction.status = 'processing'
        transaction.save()
        messages.info(request, 'Payment is being processed...')
        
    except Exception as e:
        transaction.status = 'failed'
        transaction.gateway_response = {'error': str(e)}
        transaction.save()
        
        messages.error(request, f'Payment error: {str(e)}')
    
    return redirect('billing:payment_status', transaction_id=transaction.transaction_id)


def payment_status(request, transaction_id):
    """Display payment status"""
    transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
    
    context = {
        'transaction': transaction,
        'plan': transaction.plan,
        'user': transaction.user,
    }
    
    return render(request, 'billing/payment_status.html', context)


def user_status(request):
    """Display current user status and usage"""
    mac_address = request.GET.get('mac', '')
    phone_number = request.GET.get('phone', '')
    
    wifi_user = None
    if mac_address:
        try:
            wifi_user = WifiUser.objects.get(mac_address=mac_address)
        except WifiUser.DoesNotExist:
            pass
    elif phone_number:
        try:
            wifi_user = WifiUser.objects.get(phone_number=normalize_phone_number(phone_number))
        except WifiUser.DoesNotExist:
            pass
    
    if not wifi_user:
        messages.error(request, 'User not found. Please purchase a plan first.')
        return redirect('billing:portal_home')
    
    # Get recent sessions
    recent_sessions = UserSession.objects.filter(user=wifi_user).order_by('-started_at')[:5]
    
    context = {
        'user': wifi_user,
        'plan': wifi_user.current_plan,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'billing/user_status.html', context)


def user_logout(request):
    """Handle user logout"""
    # This would typically disconnect the user from MikroTik
    messages.success(request, 'You have been logged out successfully.')
    return redirect('billing:portal_home')


# API Views
def api_plans(request):
    """API endpoint to get available plans"""
    plans = WifiPlan.objects.filter(is_active=True).order_by('price')
    plans_data = []
    
    for plan in plans:
        plans_data.append({
            'id': str(plan.id),
            'name': plan.name,
            'description': plan.description,
            'plan_type': plan.plan_type,
            'price': float(plan.price),
            'duration_minutes': plan.duration_minutes,
            'data_limit_mb': plan.data_limit_mb,
            'download_speed_kbps': plan.download_speed_kbps,
            'upload_speed_kbps': plan.upload_speed_kbps,
            'duration_display': plan.duration_display,
        })
    
    return JsonResponse({'plans': plans_data})


def api_user_status(request):
    """API endpoint to get user status"""
    mac_address = request.GET.get('mac', '')
    phone_number = request.GET.get('phone', '')
    
    if not mac_address and not phone_number:
        return JsonResponse({'error': 'MAC address or phone number required'}, status=400)
    
    wifi_user = None
    if mac_address:
        try:
            wifi_user = WifiUser.objects.get(mac_address=mac_address)
        except WifiUser.DoesNotExist:
            pass
    elif phone_number:
        try:
            wifi_user = WifiUser.objects.get(phone_number=normalize_phone_number(phone_number))
        except WifiUser.DoesNotExist:
            pass
    
    if not wifi_user:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({
        'phone_number': wifi_user.phone_number,
        'status': wifi_user.status,
        'current_plan': wifi_user.current_plan.name if wifi_user.current_plan else None,
        'plan_expires_at': wifi_user.plan_expires_at.isoformat() if wifi_user.plan_expires_at else None,
        'data_used_mb': wifi_user.data_used_mb,
        'time_remaining_minutes': wifi_user.time_remaining_minutes,
        'data_remaining_mb': wifi_user.data_remaining_mb,
        'is_active': wifi_user.is_active,
    })


# Utility functions
def validate_phone_number(phone_number):
    """Validate Kenyan phone number format"""
    # Remove spaces and special characters
    phone_number = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Check if it matches Kenyan phone number patterns
    patterns = [
        r'^254[17]\d{8}$',    # 254701234567
        r'^0[17]\d{8}$',     # 0701234567
        r'^[17]\d{8}$',      # 701234567
    ]
    
    return any(re.match(pattern, phone_number) for pattern in patterns)


def normalize_phone_number(phone_number):
    """Normalize phone number to 254 format"""
    # Remove spaces and special characters
    phone_number = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Convert to 254 format
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    return phone_number
