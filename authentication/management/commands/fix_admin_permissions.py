from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix admin user permissions to access Django admin panel'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to fix permissions for',
            default='admin'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='New password for the user (optional)',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users and their permissions',
        )
    
    def handle(self, *args, **options):
        if options['list_users']:
            self.list_all_users()
            return
        
        username = options['username']
        new_password = options['password']
        
        try:
            # Get or create the user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@broadcom.networks',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True
                }
            )
            
            if created:
                # Set default password for new user
                user.set_password(new_password or 'admin')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created new superuser: {username}')
                )
            else:
                # Update existing user permissions
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                
                if new_password:
                    user.set_password(new_password)
                    self.stdout.write(f'🔐 Updated password for user: {username}')
                
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated permissions for existing user: {username}')
                )
            
            # Display user status
            self.stdout.write('\n' + '='*50)
            self.stdout.write('USER STATUS')
            self.stdout.write('='*50)
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Is Active: {"✅" if user.is_active else "❌"}')
            self.stdout.write(f'Is Staff: {"✅" if user.is_staff else "❌"}')
            self.stdout.write(f'Is Superuser: {"✅" if user.is_superuser else "❌"}')
            self.stdout.write(f'Date Joined: {user.date_joined}')
            self.stdout.write(f'Last Login: {user.last_login or "Never"}')
            
            self.stdout.write('\n📋 WHAT THIS MEANS:')
            if user.is_staff and user.is_superuser:
                self.stdout.write('✅ User can now access Django admin panel')
                self.stdout.write('✅ User has full administrative privileges')
                self.stdout.write('✅ User can manage all system settings')
            else:
                self.stdout.write('❌ User still cannot access admin panel')
                self.stdout.write('❌ Missing required permissions')
            
            self.stdout.write('\n🔗 ACCESS URLS:')
            self.stdout.write('- Admin Panel: https://beat-production-5003.up.railway.app/admin/')
            self.stdout.write('- Custom Login: https://beat-production-5003.up.railway.app/auth/login/')
            self.stdout.write('- Dashboard: https://beat-production-5003.up.railway.app/dashboard/')
            
            if not new_password and not created:
                self.stdout.write('\n⚠️ NOTE: Password was not changed. Use --password to set a new password.')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing user permissions: {e}')
            )
    
    def list_all_users(self):
        """List all users and their permissions"""
        users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')
        
        if not users.exists():
            self.stdout.write('No users found in the database.')
            return
        
        self.stdout.write('=' * 80)
        self.stdout.write('ALL USERS IN SYSTEM')
        self.stdout.write('=' * 80)
        
        for user in users:
            status_icons = []
            if user.is_superuser:
                status_icons.append('👑 SUPERUSER')
            elif user.is_staff:
                status_icons.append('👨‍💼 STAFF')
            else:
                status_icons.append('👤 USER')
                
            if not user.is_active:
                status_icons.append('❌ INACTIVE')
            
            self.stdout.write(f'\n📧 {user.username} ({user.email or "No email"})')
            self.stdout.write(f'   Status: {" | ".join(status_icons)}')
            self.stdout.write(f'   Last Login: {user.last_login or "Never"}')
            self.stdout.write(f'   Can Access Admin: {"✅ YES" if user.is_staff else "❌ NO"}')
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Total Users: {users.count()}')
        self.stdout.write(f'Superusers: {users.filter(is_superuser=True).count()}')
        self.stdout.write(f'Staff Users: {users.filter(is_staff=True).count()}')
        self.stdout.write(f'Active Users: {users.filter(is_active=True).count()}')