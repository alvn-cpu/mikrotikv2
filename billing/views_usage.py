"""
Django Views for Usage Monitoring and Renewal Alerts
Handles AJAX requests for real-time usage tracking
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from datetime import datetime, timedelta

from .models import UserSession, TimePlan, DataPlan
from .usage_monitor import UsageMonitor, get_usage_alerts_for_mac, check_session_usage
from .utils import get_client_ip, get_mac_address_from_request

logger = logging.getLogger(__name__)

class UsageStatusView(View):
    """
    Get real-time usage status for a session
    """
    
    def get(self, request, session_id=None):
        """
        Get usage status for a specific session or current session
        """
        try:
            if session_id:
                # Get specific session
                usage_status = check_session_usage(session_id)
            else:
                # Get session for current MAC address
                mac_address = get_mac_address_from_request(request)
                if not mac_address:
                    return JsonResponse({'error': 'Unable to identify device'}, status=400)
                
                # Get active session for this MAC
                try:
                    session = UserSession.objects.filter(
                        mac_address=mac_address,
                        is_active=True
                    ).select_related('time_plan', 'data_plan').first()
                    
                    if not session:
                        return JsonResponse({'error': 'No active session found'}, status=404)
                    
                    monitor = UsageMonitor()
                    usage_status = monitor.get_session_usage_status(session)
                    
                except Exception as e:
                    logger.error(f"Error getting session for MAC {mac_address}: {e}")
                    return JsonResponse({'error': 'Failed to get session'}, status=500)
            
            # Format datetime objects for JSON serialization
            if 'start_time' in usage_status and usage_status['start_time']:
                usage_status['start_time'] = usage_status['start_time'].isoformat()
            
            return JsonResponse({
                'success': True,
                'usage_status': usage_status
            })
            
        except Exception as e:
            logger.error(f"Error getting usage status: {e}")
            return JsonResponse({'error': 'Failed to get usage status'}, status=500)

class UsageAlertsView(View):
    """
    Get usage alerts for current device/session
    """
    
    def get(self, request):
        """
        Get pending usage alerts for current device
        """
        try:
            mac_address = get_mac_address_from_request(request)
            if not mac_address:
                return JsonResponse({'error': 'Unable to identify device'}, status=400)
            
            # Get alerts for this MAC address
            alerts = get_usage_alerts_for_mac(mac_address)
            
            # Format datetime objects for JSON serialization
            for alert in alerts:
                if 'start_time' in alert and alert['start_time']:
                    alert['start_time'] = alert['start_time'].isoformat()
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            })
            
        except Exception as e:
            logger.error(f"Error getting usage alerts: {e}")
            return JsonResponse({'error': 'Failed to get alerts'}, status=500)

class RenewalOptionsView(View):
    """
    Get renewal options for a session
    """
    
    def get(self, request, session_id):
        """
        Get available renewal plans for a session
        """
        try:
            session = get_object_or_404(
                UserSession.objects.select_related('time_plan', 'data_plan'),
                id=session_id
            )
            
            monitor = UsageMonitor()
            recommendations = monitor.get_renewal_recommendations(session)
            
            return JsonResponse({
                'success': True,
                'recommendations': recommendations,
                'current_session': {
                    'id': session.id,
                    'plan_name': session.time_plan.name if session.time_plan else session.data_plan.name,
                    'plan_type': 'time' if session.time_plan else 'data'
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting renewal options for session {session_id}: {e}")
            return JsonResponse({'error': 'Failed to get renewal options'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SessionMonitoringView(View):
    """
    Handle session monitoring requests from client-side JavaScript
    """
    
    def post(self, request):
        """
        Update session usage data (for data plans)
        """
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            data_used_mb = data.get('data_used_mb', 0)
            
            if not session_id:
                return JsonResponse({'error': 'Session ID required'}, status=400)
            
            session = get_object_or_404(UserSession, id=session_id)
            
            # Update data usage if this is a data plan
            if session.data_plan and data_used_mb > 0:
                session.data_used_mb = data_used_mb
                session.save()
            
            # Get updated usage status
            monitor = UsageMonitor()
            usage_status = monitor.get_session_usage_status(session)
            
            # Format datetime for JSON
            if 'start_time' in usage_status and usage_status['start_time']:
                usage_status['start_time'] = usage_status['start_time'].isoformat()
            
            return JsonResponse({
                'success': True,
                'usage_status': usage_status
            })
            
        except Exception as e:
            logger.error(f"Error updating session monitoring: {e}")
            return JsonResponse({'error': 'Failed to update session'}, status=500)

class AllSessionsMonitorView(View):
    """
    Monitor all active sessions (Admin view)
    """
    
    def get(self, request):
        """
        Get monitoring data for all active sessions
        """
        try:
            # Check if user has admin permissions (add your auth logic here)
            if not request.user.is_staff:
                return JsonResponse({'error': 'Admin access required'}, status=403)
            
            monitor = UsageMonitor()
            alerts = monitor.monitor_all_active_sessions()
            
            # Format datetime objects for JSON serialization
            for alert in alerts:
                if 'start_time' in alert and alert['start_time']:
                    alert['start_time'] = alert['start_time'].isoformat()
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'total_active_sessions': UserSession.objects.filter(is_active=True).count(),
                'alerts_count': len(alerts),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error monitoring all sessions: {e}")
            return JsonResponse({'error': 'Failed to monitor sessions'}, status=500)

# API endpoint functions for AJAX calls
@require_http_methods(["GET"])
def get_usage_status(request):
    """
    Quick API endpoint for usage status
    """
    view = UsageStatusView()
    return view.get(request)

@require_http_methods(["GET"])
def get_usage_alerts(request):
    """
    Quick API endpoint for usage alerts
    """
    view = UsageAlertsView()
    return view.get(request)

@require_http_methods(["POST"])
@csrf_exempt
def update_session_usage(request):
    """
    Quick API endpoint for updating session usage
    """
    view = SessionMonitoringView()
    return view.post(request)

@require_http_methods(["GET"])
def get_session_recommendations(request, session_id):
    """
    Quick API endpoint for renewal recommendations
    """
    view = RenewalOptionsView()
    return view.get(request, session_id)

# Utility function for JavaScript integration
def get_client_session_data(request):
    """
    Get session data for client-side JavaScript initialization
    """
    try:
        mac_address = get_mac_address_from_request(request)
        if not mac_address:
            return None
        
        session = UserSession.objects.filter(
            mac_address=mac_address,
            is_active=True
        ).select_related('time_plan', 'data_plan').first()
        
        if not session:
            return None
        
        return {
            'session_id': session.id,
            'mac_address': session.mac_address,
            'plan_type': 'time' if session.time_plan else 'data',
            'plan_name': session.time_plan.name if session.time_plan else session.data_plan.name,
            'start_time': session.start_time.isoformat() if session.start_time else None
        }
        
    except Exception as e:
        logger.error(f"Error getting client session data: {e}")
        return None