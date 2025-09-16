#!/usr/bin/env python3
"""
Railway Deployment Script for WiFi Billing System
This script handles post-deployment tasks and setup.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_billing_system.settings')
django.setup()

def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    from django.core.management import execute_from_command_line
    
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Database migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def collect_static_files():
    """Collect static files"""
    print("🔄 Collecting static files...")
    from django.core.management import execute_from_command_line
    
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully!")
        return True
    except Exception as e:
        print(f"❌ Error collecting static files: {e}")
        return False

def create_superuser_if_none():
    """Create a superuser if none exists"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    if not User.objects.filter(is_superuser=True).exists():
        print("🔄 Creating superuser...")
        
        # Get environment variables for superuser creation
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if admin_password:
            try:
                User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
                print(f"✅ Superuser '{admin_username}' created successfully!")
                return True
            except Exception as e:
                print(f"❌ Error creating superuser: {e}")
                return False
        else:
            print("ℹ️ DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation")
            print("   You can create one manually: python manage.py createsuperuser")
            return True
    else:
        print("ℹ️ Superuser already exists, skipping creation")
        return True

def setup_site():
    """Set up Django Site for allauth integration"""
    from django.contrib.sites.models import Site
    from django.conf import settings
    
    try:
        # Update or create the Site with SITE_ID = 1
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': 'beat-production-5003.up.railway.app',
                'name': 'BROADCOM NETWORKS'
            }
        )
        
        if not created:
            # Update existing site
            site.domain = 'beat-production-5003.up.railway.app'
            site.name = 'BROADCOM NETWORKS'
            site.save()
            print(f"✅ Updated Site: {site.name} ({site.domain})")
        else:
            print(f"✅ Created Site: {site.name} ({site.domain})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up site: {e}")
        return False

def create_sample_data():
    """Create sample WiFi plans if none exist"""
    from billing.models import WifiPlan
    
    if not WifiPlan.objects.exists():
        print("🔄 Creating sample WiFi plans...")
        
        try:
            # Create sample plans
            plans_data = [
                {
                    'name': '30 Minutes',
                    'description': 'Quick browsing session',
                    'plan_type': 'time',
                    'price': 10.00,
                    'duration_minutes': 30,
                    'download_speed_kbps': 2048,
                    'upload_speed_kbps': 1024,
                },
                {
                    'name': '100MB Data',
                    'description': 'Light data usage',
                    'plan_type': 'data',
                    'price': 15.00,
                    'data_limit_mb': 100,
                    'download_speed_kbps': 4096,
                    'upload_speed_kbps': 2048,
                },
                {
                    'name': '1 Hour',
                    'description': 'Standard browsing session',
                    'plan_type': 'time',
                    'price': 20.00,
                    'duration_minutes': 60,
                    'download_speed_kbps': 2048,
                    'upload_speed_kbps': 1024,
                },
                {
                    'name': '24 Hours',
                    'description': 'All-day unlimited access',
                    'plan_type': 'unlimited',
                    'price': 100.00,
                    'duration_minutes': 1440,
                    'download_speed_kbps': 8192,
                    'upload_speed_kbps': 4096,
                },
            ]
            
            for plan_data in plans_data:
                WifiPlan.objects.create(**plan_data)
            
            print(f"✅ Created {len(plans_data)} sample WiFi plans!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            return False
    else:
        print("ℹ️ WiFi plans already exist, skipping sample data creation")
        return True

def main():
    """Main deployment function"""
    print("🚀 Starting WiFi Billing System deployment...")
    print(f"📍 Environment: {'Production' if not os.environ.get('DEBUG', 'False').lower() == 'true' else 'Development'}")
    
    success = True
    
    # Run migrations
    if not run_migrations():
        success = False
    
    # Collect static files
    if not collect_static_files():
        success = False
    
    # Set up Django Site for allauth
    if not setup_site():
        success = False
    
    # Create superuser if needed
    if not create_superuser_if_none():
        success = False
    
    # Create sample data if needed
    if not create_sample_data():
        success = False
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        print("\n📋 Next steps:")
        print("1. Set up your environment variables in Railway")
        print("2. Configure your domain in ALLOWED_HOSTS")
        print("3. Add your MikroTik router configurations")
        print("4. Test the payment integration")
        print("5. Configure your KCB Buni credentials")
        
        return 0
    else:
        print("\n❌ Deployment completed with errors!")
        return 1

if __name__ == '__main__':
    sys.exit(main())