from django.core.management.base import BaseCommand
from django.utils import timezone
from mikrotik_integration.models import RouterConfig, ActiveUser
from mikrotik_integration.services import MikroTikManager, disconnect_expired_users
from billing.models import WifiUser
import time


class Command(BaseCommand):
    help = 'Monitor WiFi sessions and manage user connections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once instead of continuously',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting WiFi session monitoring...')
        
        if options['once']:
            self.monitor_once()
        else:
            self.monitor_continuously(options['interval'])
    
    def monitor_once(self):
        """Run monitoring tasks once"""
        try:
            # Get active routers
            routers = RouterConfig.objects.filter(is_active=True)
            
            if not routers.exists():
                self.stdout.write(self.style.WARNING('No active routers found'))
                return
            
            for router in routers:
                self.stdout.write(f'Monitoring router: {router.name} ({router.host})')
                
                try:
                    with MikroTikManager(router) as mikrotik:
                        # Update active users in database
                        active_count = mikrotik.update_active_users_in_db()
                        self.stdout.write(f'  ✓ Updated {active_count} active users')
                        
                        # Sync with RADIUS accounting
                        synced_count = mikrotik.sync_radius_accounting()
                        self.stdout.write(f'  ✓ Synced {synced_count} RADIUS accounting records')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error monitoring {router.name}: {str(e)}')
                    )
            
            # Disconnect expired users
            self.stdout.write('\\nChecking for expired users...')
            expired_count = disconnect_expired_users()
            if expired_count > 0:
                self.stdout.write(f'  ✓ Disconnected {expired_count} expired users')
            else:
                self.stdout.write('  - No expired users found')
            
            # Display session summary
            self.display_session_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Monitoring error: {str(e)}'))
    
    def monitor_continuously(self, interval):
        """Run monitoring continuously"""
        self.stdout.write(f'Monitoring every {interval} seconds. Press Ctrl+C to stop.')
        
        try:
            while True:
                self.stdout.write(f'\\n[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Running monitoring cycle...')
                self.monitor_once()
                
                self.stdout.write(f'Waiting {interval} seconds...')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write('\\nStopping session monitoring...')
    
    def display_session_summary(self):
        """Display current session summary"""
        self.stdout.write('\\n--- Session Summary ---')
        
        # Count users by status
        total_users = WifiUser.objects.count()
        active_users = WifiUser.objects.filter(status='active').count()
        pending_users = WifiUser.objects.filter(status='pending').count()
        expired_users = WifiUser.objects.filter(status='expired').count()
        
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'  Active: {active_users}')
        self.stdout.write(f'  Pending: {pending_users}')
        self.stdout.write(f'  Expired: {expired_users}')
        
        # Count active sessions per router
        routers = RouterConfig.objects.filter(is_active=True)
        for router in routers:
            active_sessions = ActiveUser.objects.filter(router=router, is_active=True).count()
            self.stdout.write(f'{router.name}: {active_sessions} active sessions')
        
        # Show users expiring soon (next 30 minutes)
        soon_expiring = WifiUser.objects.filter(
            status='active',
            plan_expires_at__lte=timezone.now() + timezone.timedelta(minutes=30),
            plan_expires_at__gt=timezone.now()
        ).count()
        
        if soon_expiring > 0:
            self.stdout.write(f'⚠️  {soon_expiring} users expiring within 30 minutes')
        
        self.stdout.write('----------------------')