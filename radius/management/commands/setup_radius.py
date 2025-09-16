from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import WifiPlan
from radius.models import (
    NasClient, RadiusGroup, RadiusGroupReply, 
    RadiusUser, RadiusUserGroup, RadiusAccounting
)
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Set up RADIUS server integration with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up RADIUS integration...')
        
        # Create NAS clients (MikroTik routers)
        self.stdout.write('Creating NAS clients...')
        nas_clients = [
            {
                'shortname': 'MainRouter',
                'nasname': '192.168.1.1',
                'type': 'mikrotik',
                'secret': 'radius123',
                'description': 'Main MikroTik Router',
                'is_active': True,
            },
            {
                'shortname': 'SecondaryRouter',
                'nasname': '192.168.1.2',
                'type': 'mikrotik',
                'secret': 'radius456',
                'description': 'Secondary MikroTik Router',
                'is_active': True,
            }
        ]
        
        for nas_data in nas_clients:
            nas, created = NasClient.objects.get_or_create(
                shortname=nas_data['shortname'],
                defaults=nas_data
            )
            if created:
                self.stdout.write(f'  ✓ Created NAS client: {nas.shortname}')
            else:
                self.stdout.write(f'  - NAS client already exists: {nas.shortname}')
        
        # Create RADIUS groups for each WiFi plan
        self.stdout.write('\\nCreating RADIUS groups...')
        plans = WifiPlan.objects.filter(is_active=True)
        
        for plan in plans:
            # Create group name based on plan
            group_name = f"plan_{plan.name.lower().replace(' ', '_')}"
            
            # Create bandwidth group
            bandwidth_group, created = RadiusGroup.objects.get_or_create(
                groupname=group_name,
                attribute='Mikrotik-Rate-Limit',
                defaults={
                    'wifi_plan': plan,
                    'op': ':=',
                    'value': f"{plan.upload_speed_kbps}k/{plan.download_speed_kbps}k"
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Created RADIUS group: {group_name}')
                
                # Create group reply attributes
                replies = []
                
                # Session timeout for time-based plans
                if plan.plan_type == 'time' and plan.duration_minutes:
                    replies.append({
                        'attribute': 'Session-Timeout',
                        'value': str(plan.duration_minutes * 60)  # Convert to seconds
                    })
                
                # Data limit for data-based plans
                if plan.plan_type == 'data' and plan.data_limit_mb:
                    replies.append({
                        'attribute': 'Mikrotik-Total-Limit',
                        'value': str(plan.data_limit_mb * 1024 * 1024)  # Convert to bytes
                    })
                
                # Add idle timeout
                replies.append({
                    'attribute': 'Idle-Timeout',
                    'value': '300'  # 5 minutes
                })
                
                # Create reply attributes
                for reply_data in replies:
                    RadiusGroupReply.objects.create(
                        groupname=group_name,
                        attribute=reply_data['attribute'],
                        op=':=',
                        value=reply_data['value']
                    )
                    
                self.stdout.write(f'    - Added {len(replies)} reply attributes')
            else:
                self.stdout.write(f'  - Group already exists: {group_name}')
        
        # Create sample accounting data
        self.stdout.write('\\nCreating sample accounting data...')
        self.create_sample_accounting()
        
        self.stdout.write(self.style.SUCCESS('\\n✓ RADIUS integration setup completed!'))
        self.stdout.write('\\nNext steps:')
        self.stdout.write('1. Configure FreeRADIUS to use this Django database')
        self.stdout.write('2. Set up MikroTik to use RADIUS authentication')
        self.stdout.write('3. Configure hotspot to redirect to captive portal')
        
    def create_sample_accounting(self):
        """Create sample RADIUS accounting data for dashboard"""
        sample_sessions = [
            {
                'username': 'user_12345678',
                'acctsessionid': f'sess_{random.randint(1000, 9999)}',
                'nasipaddress': '192.168.1.1',
                'framedipaddress': f'10.0.0.{random.randint(10, 250)}',
                'callingstationid': f'AA:BB:CC:DD:EE:{random.randint(10, 99):02X}',
                'acctstarttime': timezone.now() - timedelta(minutes=random.randint(30, 120)),
                'acctsessiontime': random.randint(600, 3600),  # 10 minutes to 1 hour
                'acctinputoctets': random.randint(1024*1024, 50*1024*1024),  # 1MB to 50MB
                'acctoutputoctets': random.randint(5*1024*1024, 200*1024*1024),  # 5MB to 200MB
                'acctterminatecause': 'User-Request'
            }
            for _ in range(10)
        ]
        
        for session_data in sample_sessions:
            # Create unique session ID
            session_data['acctuniqueid'] = f"unique_{random.randint(100000, 999999)}"
            session_data['acctstoptime'] = session_data['acctstarttime'] + timedelta(seconds=session_data['acctsessiontime'])
            
            RadiusAccounting.objects.get_or_create(
                acctuniqueid=session_data['acctuniqueid'],
                defaults=session_data
            )
        
        self.stdout.write('  ✓ Created 10 sample accounting sessions')
        
        # Create some active sessions (no stop time)
        active_sessions = 3
        for i in range(active_sessions):
            session_data = {
                'username': f'active_user_{i+1}',
                'acctsessionid': f'active_sess_{random.randint(1000, 9999)}',
                'acctuniqueid': f'active_unique_{random.randint(100000, 999999)}',
                'nasipaddress': '192.168.1.1',
                'framedipaddress': f'10.0.0.{random.randint(100, 200)}',
                'callingstationid': f'BB:CC:DD:EE:FF:{random.randint(10, 99):02X}',
                'acctstarttime': timezone.now() - timedelta(minutes=random.randint(5, 60)),
                'acctinputoctets': random.randint(512*1024, 10*1024*1024),
                'acctoutputoctets': random.randint(2*1024*1024, 50*1024*1024),
            }
            
            RadiusAccounting.objects.get_or_create(
                acctuniqueid=session_data['acctuniqueid'],
                defaults=session_data
            )
        
        self.stdout.write(f'  ✓ Created {active_sessions} active sessions')