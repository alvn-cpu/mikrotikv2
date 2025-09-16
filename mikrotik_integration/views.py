from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from .models import RouterConfig, ActiveUser, RouterCommand
from .services import MikroTikManager, disconnect_expired_users
from billing.models import WifiUser
from radius.models import RadiusAccounting
import json


@staff_member_required
def router_status_api(request):
    """API endpoint for real-time router status"""
    routers_data = []
    
    for router in RouterConfig.objects.filter(is_active=True):
        # Get active sessions count
        active_sessions = ActiveUser.objects.filter(
            router=router, 
            is_active=True
        ).count()
        
        # Get recent commands
        recent_commands = RouterCommand.objects.filter(
            router=router
        ).order_by('-executed_at')[:5]
        
        router_data = {
            'id': router.id,
            'name': router.name,
            'host': router.host,
            'status': router.connection_status,
            'last_connected': router.last_connected.isoformat() if router.last_connected else None,
            'active_sessions': active_sessions,
            'recent_commands': [
                {
                    'type': cmd.command_type,
                    'success': cmd.success,
                    'executed_at': cmd.executed_at.isoformat(),
                    'error': cmd.error_message if not cmd.success else None
                }
                for cmd in recent_commands
            ]
        }
        routers_data.append(router_data)
    
    return JsonResponse({
        'routers': routers_data,
        'timestamp': timezone.now().isoformat()
    })


@staff_member_required
def active_sessions_api(request):
    """API endpoint for active sessions data"""
    sessions_data = []
    
    # Get all active sessions
    active_sessions = ActiveUser.objects.filter(
        is_active=True
    ).select_related('wifi_user', 'router').order_by('-login_time')[:50]
    
    for session in active_sessions:
        session_data = {
            'id': session.id,
            'username': session.username,
            'phone_number': session.wifi_user.phone_number if session.wifi_user else 'Unknown',
            'ip_address': session.ip_address,
            'mac_address': session.mac_address,
            'router': session.router.name,
            'login_time': session.login_time.isoformat() if session.login_time else None,
            'uptime': session.uptime,
            'data_usage_mb': session.total_mb,
            'plan': session.wifi_user.current_plan.name if session.wifi_user and session.wifi_user.current_plan else 'N/A',
            'expires_at': session.wifi_user.plan_expires_at.isoformat() if session.wifi_user and session.wifi_user.plan_expires_at else None
        }
        sessions_data.append(session_data)
    
    return JsonResponse({
        'sessions': sessions_data,
        'total_count': len(sessions_data),
        'timestamp': timezone.now().isoformat()
    })


@staff_member_required
def session_statistics_api(request):
    """API endpoint for session statistics"""
    # Current statistics
    total_users = WifiUser.objects.count()
    active_users = WifiUser.objects.filter(status='active').count()
    active_sessions = ActiveUser.objects.filter(is_active=True).count()
    
    # Users by status
    status_stats = {
        'active': WifiUser.objects.filter(status='active').count(),
        'pending': WifiUser.objects.filter(status='pending').count(),
        'expired': WifiUser.objects.filter(status='expired').count(),
        'disabled': WifiUser.objects.filter(status='disabled').count()
    }
    
    # Sessions by router
    router_stats = []
    for router in RouterConfig.objects.filter(is_active=True):
        router_sessions = ActiveUser.objects.filter(
            router=router, 
            is_active=True
        ).count()
        router_stats.append({
            'name': router.name,
            'sessions': router_sessions,
            'status': router.connection_status
        })
    
    # Users expiring soon
    soon_expiring = WifiUser.objects.filter(
        status='active',
        plan_expires_at__lte=timezone.now() + timezone.timedelta(minutes=30),
        plan_expires_at__gt=timezone.now()
    ).count()
    
    # Data usage in last 24 hours
    recent_usage = RadiusAccounting.objects.filter(
        acctstarttime__gte=timezone.now() - timezone.timedelta(hours=24)
    ).aggregate(
        total_bytes=models.Sum(models.F('acctinputoctets') + models.F('acctoutputoctets'))
    )['total_bytes'] or 0
    
    return JsonResponse({
        'overview': {
            'total_users': total_users,
            'active_users': active_users,
            'active_sessions': active_sessions,
            'soon_expiring': soon_expiring
        },
        'status_breakdown': status_stats,
        'router_breakdown': router_stats,
        'data_usage_24h_mb': round(recent_usage / (1024 * 1024), 2),
        'timestamp': timezone.now().isoformat()
    })


@staff_member_required
@csrf_exempt
def disconnect_user_api(request):
    """API endpoint to disconnect a user"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({'error': 'Username required'}, status=400)
        
        # Find the user
        try:
            wifi_user = WifiUser.objects.get(mikrotik_username=username)
        except WifiUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Get the router
        router = RouterConfig.objects.filter(is_active=True).first()
        if not router:
            return JsonResponse({'error': 'No active router found'}, status=500)
        
        # Disconnect the user
        with MikroTikManager(router) as mikrotik:
            success = mikrotik.disconnect_user(username)
            
            if success:
                # Update user status
                wifi_user.status = 'disabled'
                wifi_user.save()
                
                # Update active session
                ActiveUser.objects.filter(
                    wifi_user=wifi_user,
                    is_active=True
                ).update(is_active=False)
                
                return JsonResponse({
                    'success': True,
                    'message': f'User {username} disconnected successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'User {username} not found in active sessions'
                })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def sync_sessions_api(request):
    """API endpoint to trigger session sync"""
    try:
        total_synced = 0
        errors = []
        
        for router in RouterConfig.objects.filter(is_active=True):
            try:
                with MikroTikManager(router) as mikrotik:
                    synced = mikrotik.update_active_users_in_db()
                    total_synced += synced
            except Exception as e:
                errors.append(f'{router.name}: {str(e)}')
        
        # Check for expired users
        expired_count = disconnect_expired_users()
        
        response = {
            'success': True,
            'synced_sessions': total_synced,
            'disconnected_expired': expired_count,
            'timestamp': timezone.now().isoformat()
        }
        
        if errors:
            response['errors'] = errors
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
