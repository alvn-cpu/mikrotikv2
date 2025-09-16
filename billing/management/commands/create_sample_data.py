from django.core.management.base import BaseCommand
from billing.models import WifiPlan
from mikrotik_integration.models import RouterConfig, UserProfile


class Command(BaseCommand):
    help = 'Create sample data for WiFi billing system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample WiFi plans...')
        
        # Create sample WiFi plans
        plans_data = [
            {
                'name': '30 Minutes',
                'description': 'Perfect for quick browsing and checking messages',
                'plan_type': 'time',
                'price': 10.00,
                'duration_minutes': 30,
                'download_speed_kbps': 1024,  # 1 Mbps
                'upload_speed_kbps': 512,     # 512 Kbps
            },
            {
                'name': '1 Hour',
                'description': 'Great for social media and light streaming',
                'plan_type': 'time',
                'price': 20.00,
                'duration_minutes': 60,
                'download_speed_kbps': 2048,  # 2 Mbps
                'upload_speed_kbps': 1024,    # 1 Mbps
            },
            {
                'name': '3 Hours',
                'description': 'Ideal for work and extended browsing',
                'plan_type': 'time',
                'price': 50.00,
                'duration_minutes': 180,
                'download_speed_kbps': 4096,  # 4 Mbps
                'upload_speed_kbps': 2048,    # 2 Mbps
            },
            {
                'name': '24 Hours',
                'description': 'Full day access for heavy users',
                'plan_type': 'time',
                'price': 100.00,
                'duration_minutes': 1440,
                'download_speed_kbps': 8192,  # 8 Mbps
                'upload_speed_kbps': 4096,    # 4 Mbps
            },
            {
                'name': '100MB Data',
                'description': 'Data-based plan for light usage',
                'plan_type': 'data',
                'price': 15.00,
                'data_limit_mb': 100,
                'download_speed_kbps': 2048,
                'upload_speed_kbps': 1024,
            },
            {
                'name': '500MB Data',
                'description': 'Data-based plan for moderate usage',
                'plan_type': 'data',
                'price': 50.00,
                'data_limit_mb': 500,
                'download_speed_kbps': 4096,
                'upload_speed_kbps': 2048,
            },
        ]
        
        created_plans = 0
        for plan_data in plans_data:
            plan, created = WifiPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_plans += 1
                self.stdout.write(f'  ✓ Created plan: {plan.name}')
            else:
                self.stdout.write(f'  - Plan already exists: {plan.name}')
        
        self.stdout.write(f'Created {created_plans} new WiFi plans')
        
        # Create sample router configuration
        self.stdout.write('\\nCreating sample router configuration...')
        router, created = RouterConfig.objects.get_or_create(
            name='Main Router',
            defaults={
                'host': '192.168.1.1',
                'api_port': 8728,
                'username': 'admin',
                'password': 'change_this_password',
                'hotspot_interface': 'wlan1',
                'address_pool': 'dhcp_pool1',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('  ✓ Created router configuration: Main Router')
        else:
            self.stdout.write('  - Router configuration already exists: Main Router')
        
        # Create sample user profiles
        self.stdout.write('\\nCreating sample user profiles...')
        profiles_data = [
            {
                'name': 'Basic',
                'download_limit': '1M',
                'upload_limit': '512k',
                'session_timeout': '1h',
                'idle_timeout': '5m',
                'shared_users': 1,
            },
            {
                'name': 'Premium',
                'download_limit': '5M',
                'upload_limit': '2M',
                'session_timeout': '24h',
                'idle_timeout': '10m',
                'shared_users': 2,
            },
            {
                'name': 'VIP',
                'download_limit': '10M',
                'upload_limit': '5M',
                'session_timeout': '0',  # No timeout
                'idle_timeout': '30m',
                'shared_users': 5,
            },
        ]
        
        created_profiles = 0
        for profile_data in profiles_data:
            profile, created = UserProfile.objects.get_or_create(
                name=profile_data['name'],
                defaults=profile_data
            )
            if created:
                created_profiles += 1
                self.stdout.write(f'  ✓ Created user profile: {profile.name}')
            else:
                self.stdout.write(f'  - User profile already exists: {profile.name}')
        
        self.stdout.write(f'Created {created_profiles} new user profiles')
        
        self.stdout.write(self.style.SUCCESS('\\n✓ Sample data creation completed successfully!'))
        self.stdout.write('\\nYou can now:')
        self.stdout.write('1. Access the admin panel at http://127.0.0.1:8000/admin/')
        self.stdout.write('   Username: admin, Password: admin')
        self.stdout.write('2. View and manage WiFi plans, users, and transactions')
        self.stdout.write('3. Configure your MikroTik router settings')