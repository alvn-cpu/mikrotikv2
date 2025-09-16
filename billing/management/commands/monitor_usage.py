"""
Django Management Command for Periodic Usage Monitoring
Runs as background task to check usage and send alerts
"""

import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from billing.usage_monitor import monitor_all_sessions
from billing.models import UserSession

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitor usage and send alerts for active sessions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        
        parser.add_argument(
            '--run-once',
            action='store_true',
            help='Run once instead of continuously'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--email-alerts',
            action='store_true',
            help='Send email alerts for critical usage'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['run_once']
        verbose = options['verbose']
        email_alerts = options['email_alerts']
        
        if verbose:
            logger.setLevel(logging.INFO)
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting Usage Monitor (interval: {interval}s)')
        )
        
        if run_once:
            self.check_usage_once(email_alerts, verbose)
        else:
            self.monitor_continuously(interval, email_alerts, verbose)
    
    def check_usage_once(self, email_alerts, verbose):
        """Run usage monitoring once"""
        try:
            start_time = time.time()
            alerts = monitor_all_sessions()
            
            if verbose:
                self.stdout.write(f'📊 Checked {UserSession.objects.filter(is_active=True).count()} active sessions')
                self.stdout.write(f'🚨 Found {len(alerts)} alerts')
            
            if alerts:
                self.process_alerts(alerts, email_alerts, verbose)
            
            duration = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(f'✅ Check completed in {duration:.2f}s')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during usage check: {e}')
            )
            logger.error(f'Usage monitoring error: {e}', exc_info=True)
    
    def monitor_continuously(self, interval, email_alerts, verbose):
        """Run continuous monitoring"""
        self.stdout.write(f'🔄 Starting continuous monitoring...')
        
        try:
            while True:
                self.check_usage_once(email_alerts, verbose)
                
                if verbose:
                    next_check = timezone.now() + timezone.timedelta(seconds=interval)
                    self.stdout.write(f'⏰ Next check at {next_check.strftime("%H:%M:%S")}')
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('🛑 Monitoring stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Fatal error in monitoring: {e}')
            )
            logger.error(f'Fatal usage monitoring error: {e}', exc_info=True)
    
    def process_alerts(self, alerts, email_alerts, verbose):
        """Process and optionally send alerts"""
        alert_counts = {'warning': 0, 'critical': 0, 'final': 0}
        
        for alert in alerts:
            alert_level = alert.get('alert_level', 'warning')
            alert_counts[alert_level] += 1
            
            if verbose:
                self.stdout.write(
                    f'🚨 {alert_level.upper()}: {alert.get("plan_name", "Unknown")} '
                    f'- {alert.get("percentage_used", 0):.1f}% used'
                )
            
            # Send email for critical and final alerts
            if email_alerts and alert_level in ['critical', 'final']:
                self.send_email_alert(alert)
        
        # Summary
        total_alerts = sum(alert_counts.values())
        if total_alerts > 0:
            self.stdout.write(
                f'📋 Alert Summary: {alert_counts["warning"]} warnings, '
                f'{alert_counts["critical"]} critical, {alert_counts["final"]} final'
            )
    
    def send_email_alert(self, alert):
        """Send email alert for critical usage"""
        try:
            if not hasattr(settings, 'EMAIL_HOST') or not settings.EMAIL_HOST:
                return  # Email not configured
            
            alert_level = alert.get('alert_level', 'critical')
            plan_name = alert.get('plan_name', 'Unknown Plan')
            percentage = alert.get('percentage_used', 0)
            session_id = alert.get('session_id')
            mac_address = alert.get('mac_address', 'Unknown')
            
            # Format remaining info
            if alert.get('session_type') == 'time':
                remaining = f"{alert.get('remaining_minutes', 0):.0f} minutes"
            else:
                remaining_mb = alert.get('remaining_mb', 0)
                if remaining_mb > 1024:
                    remaining = f"{remaining_mb / 1024:.1f} GB"
                else:
                    remaining = f"{remaining_mb:.0f} MB"
            
            subject = f'WiFi Usage {alert_level.title()} Alert - {plan_name}'
            
            message = f"""
WiFi Usage Alert - {alert_level.title()} Level

Plan: {plan_name}
Usage: {percentage:.1f}% ({remaining} remaining)
Device: {mac_address}
Session ID: {session_id}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

{'🔴 URGENT: Session will end soon!' if alert_level == 'final' else '⚠️ High usage detected - consider renewal'}

View session details: {settings.BASE_URL}/admin/billing/usersession/{session_id}/
            """.strip()
            
            # Send to admin emails
            admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=False
                )
                
                self.stdout.write(f'📧 Email alert sent for session {session_id}')
            
        except Exception as e:
            logger.error(f'Error sending email alert: {e}', exc_info=True)
            self.stdout.write(
                self.style.WARNING(f'⚠️ Failed to send email alert: {e}')
            )