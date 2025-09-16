"""
Advanced Usage Monitoring System
Tracks time and data consumption and triggers intelligent alerts
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from .models import UserSession, TimePlan, DataPlan, PaymentRecord

logger = logging.getLogger(__name__)

class UsageMonitor:
    """
    Comprehensive usage monitoring and alert system
    """
    
    # Alert thresholds (percentage of usage)
    ALERT_THRESHOLDS = {
        'warning': 75,      # 75% - First warning
        'critical': 90,     # 90% - Critical alert with renewal options
        'final': 95        # 95% - Final warning before cutoff
    }
    
    # Cache keys for usage tracking
    CACHE_KEYS = {
        'usage': 'usage_data_{session_id}',
        'alerts_sent': 'alerts_sent_{session_id}',
        'last_check': 'last_usage_check_{session_id}'
    }
    
    def __init__(self):
        self.current_time = timezone.now()
    
    def calculate_time_usage_percentage(self, session: UserSession) -> Tuple[float, Dict]:
        """
        Calculate time-based usage percentage and remaining time
        
        Returns:
            Tuple of (percentage_used, usage_info_dict)
        """
        if not session.time_plan:
            return 0.0, {}
        
        # Calculate total session duration in minutes
        total_duration_minutes = session.time_plan.duration_minutes
        
        # Calculate time elapsed since session start
        if session.start_time:
            time_elapsed = self.current_time - session.start_time
            elapsed_minutes = time_elapsed.total_seconds() / 60
        else:
            elapsed_minutes = 0
        
        # Handle active vs paused sessions
        if session.is_active:
            current_elapsed = elapsed_minutes
        else:
            # Use stored usage if session is paused/ended
            current_elapsed = session.time_used_minutes or 0
        
        # Calculate percentage
        if total_duration_minutes > 0:
            percentage_used = min((current_elapsed / total_duration_minutes) * 100, 100)
        else:
            percentage_used = 0
        
        # Calculate remaining time
        remaining_minutes = max(total_duration_minutes - current_elapsed, 0)
        remaining_hours = remaining_minutes / 60
        
        usage_info = {
            'total_minutes': total_duration_minutes,
            'used_minutes': current_elapsed,
            'remaining_minutes': remaining_minutes,
            'remaining_hours': remaining_hours,
            'percentage_used': percentage_used,
            'plan_name': session.time_plan.name,
            'plan_price': session.time_plan.price,
            'session_type': 'time'
        }
        
        return percentage_used, usage_info
    
    def calculate_data_usage_percentage(self, session: UserSession) -> Tuple[float, Dict]:
        """
        Calculate data-based usage percentage and remaining data
        
        Returns:
            Tuple of (percentage_used, usage_info_dict)
        """
        if not session.data_plan:
            return 0.0, {}
        
        # Get total data allowance in MB
        total_data_mb = session.data_plan.data_limit_mb
        
        # Get current data usage (you might need to integrate with your bandwidth monitoring)
        used_data_mb = session.data_used_mb or 0
        
        # Calculate percentage
        if total_data_mb > 0:
            percentage_used = min((used_data_mb / total_data_mb) * 100, 100)
        else:
            percentage_used = 0
        
        # Calculate remaining data
        remaining_data_mb = max(total_data_mb - used_data_mb, 0)
        remaining_data_gb = remaining_data_mb / 1024
        
        usage_info = {
            'total_mb': total_data_mb,
            'used_mb': used_data_mb,
            'remaining_mb': remaining_data_mb,
            'remaining_gb': remaining_data_gb,
            'percentage_used': percentage_used,
            'plan_name': session.data_plan.name,
            'plan_price': session.data_plan.price,
            'session_type': 'data'
        }
        
        return percentage_used, usage_info
    
    def get_session_usage_status(self, session: UserSession) -> Dict:
        """
        Get comprehensive usage status for a session
        """
        if session.time_plan:
            percentage, usage_info = self.calculate_time_usage_percentage(session)
        elif session.data_plan:
            percentage, usage_info = self.calculate_data_usage_percentage(session)
        else:
            return {'error': 'No plan associated with session'}
        
        # Determine alert level
        alert_level = self.get_alert_level(percentage)
        
        # Check if session should be terminated
        should_terminate = percentage >= 100
        
        usage_status = {
            **usage_info,
            'alert_level': alert_level,
            'should_alert': alert_level is not None,
            'should_terminate': should_terminate,
            'session_id': session.id,
            'mac_address': session.mac_address,
            'user_ip': session.user_ip,
            'start_time': session.start_time,
            'is_active': session.is_active
        }
        
        return usage_status
    
    def get_alert_level(self, percentage_used: float) -> Optional[str]:
        """
        Determine alert level based on usage percentage
        """
        if percentage_used >= self.ALERT_THRESHOLDS['final']:
            return 'final'
        elif percentage_used >= self.ALERT_THRESHOLDS['critical']:
            return 'critical'
        elif percentage_used >= self.ALERT_THRESHOLDS['warning']:
            return 'warning'
        return None
    
    def should_send_alert(self, session: UserSession, alert_level: str) -> bool:
        """
        Check if alert should be sent (avoid spam)
        """
        cache_key = self.CACHE_KEYS['alerts_sent'].format(session_id=session.id)
        sent_alerts = cache.get(cache_key, [])
        
        # Don't send same level alert twice
        if alert_level in sent_alerts:
            return False
        
        return True
    
    def mark_alert_sent(self, session: UserSession, alert_level: str):
        """
        Mark alert as sent to prevent duplicates
        """
        cache_key = self.CACHE_KEYS['alerts_sent'].format(session_id=session.id)
        sent_alerts = cache.get(cache_key, [])
        
        if alert_level not in sent_alerts:
            sent_alerts.append(alert_level)
            # Cache for the duration of the session + 1 hour
            timeout = 3600  # 1 hour
            cache.set(cache_key, sent_alerts, timeout)
    
    def get_renewal_recommendations(self, current_session: UserSession) -> List[Dict]:
        """
        Get recommended plans for renewal based on current usage patterns
        """
        recommendations = []
        
        if current_session.time_plan:
            # Get similar or higher time plans
            similar_plans = TimePlan.objects.filter(
                is_active=True
            ).order_by('duration_minutes')
            
            for plan in similar_plans:
                recommendations.append({
                    'id': plan.id,
                    'name': plan.name,
                    'price': plan.price,
                    'duration': plan.duration_display(),
                    'type': 'time',
                    'recommended': plan.duration_minutes >= current_session.time_plan.duration_minutes
                })
        
        elif current_session.data_plan:
            # Get similar or higher data plans
            similar_plans = DataPlan.objects.filter(
                is_active=True
            ).order_by('data_limit_mb')
            
            for plan in similar_plans:
                recommendations.append({
                    'id': plan.id,
                    'name': plan.name,
                    'price': plan.price,
                    'data_limit': f"{plan.data_limit_mb} MB",
                    'type': 'data',
                    'recommended': plan.data_limit_mb >= current_session.data_plan.data_limit_mb
                })
        
        # Sort recommendations - recommended first, then by price
        recommendations.sort(key=lambda x: (not x.get('recommended', False), float(x['price'])))
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def monitor_all_active_sessions(self) -> List[Dict]:
        """
        Monitor all active sessions and return those needing alerts
        """
        active_sessions = UserSession.objects.filter(
            is_active=True,
            end_time__isnull=True
        ).select_related('time_plan', 'data_plan')
        
        sessions_needing_alerts = []
        
        for session in active_sessions:
            try:
                usage_status = self.get_session_usage_status(session)
                
                if usage_status.get('should_alert'):
                    alert_level = usage_status['alert_level']
                    
                    # Check if we should send this alert
                    if self.should_send_alert(session, alert_level):
                        # Get renewal recommendations
                        usage_status['recommendations'] = self.get_renewal_recommendations(session)
                        sessions_needing_alerts.append(usage_status)
                        
                        # Mark alert as sent
                        self.mark_alert_sent(session, alert_level)
                
                # Terminate session if usage is 100%
                if usage_status.get('should_terminate'):
                    self.terminate_session(session)
                    
            except Exception as e:
                logger.error(f"Error monitoring session {session.id}: {e}")
        
        return sessions_needing_alerts
    
    def terminate_session(self, session: UserSession):
        """
        Terminate a session that has exceeded its limits
        """
        try:
            with transaction.atomic():
                session.is_active = False
                session.end_time = self.current_time
                session.save()
                
                # Log termination
                logger.info(f"Session {session.id} terminated due to usage limit exceeded")
                
        except Exception as e:
            logger.error(f"Error terminating session {session.id}: {e}")
    
    def get_usage_summary_for_session(self, session_id: int) -> Dict:
        """
        Get detailed usage summary for a specific session
        """
        try:
            session = UserSession.objects.select_related(
                'time_plan', 'data_plan'
            ).get(id=session_id)
            
            usage_status = self.get_session_usage_status(session)
            
            if usage_status.get('should_alert'):
                usage_status['recommendations'] = self.get_renewal_recommendations(session)
            
            return usage_status
            
        except UserSession.DoesNotExist:
            return {'error': 'Session not found'}
        except Exception as e:
            logger.error(f"Error getting usage summary for session {session_id}: {e}")
            return {'error': 'Failed to get usage summary'}

# Utility functions for easy integration
def check_session_usage(session_id: int) -> Dict:
    """
    Quick function to check usage for a specific session
    """
    monitor = UsageMonitor()
    return monitor.get_usage_summary_for_session(session_id)

def monitor_all_sessions() -> List[Dict]:
    """
    Quick function to monitor all active sessions
    """
    monitor = UsageMonitor()
    return monitor.monitor_all_active_sessions()

def get_usage_alerts_for_mac(mac_address: str) -> List[Dict]:
    """
    Get usage alerts for a specific MAC address
    """
    try:
        sessions = UserSession.objects.filter(
            mac_address=mac_address,
            is_active=True
        ).select_related('time_plan', 'data_plan')
        
        monitor = UsageMonitor()
        alerts = []
        
        for session in sessions:
            usage_status = monitor.get_session_usage_status(session)
            if usage_status.get('should_alert'):
                usage_status['recommendations'] = monitor.get_renewal_recommendations(session)
                alerts.append(usage_status)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts for MAC {mac_address}: {e}")
        return []