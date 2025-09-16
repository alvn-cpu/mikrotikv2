from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Create admin user for Railway deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Admin username (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Admin email (default: admin@example.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password (if not provided, will use environment variable or prompt)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists!')
            )
            return

        # Get password from environment variable or prompt
        if not password:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not password:
            password = 'admin123'  # Default fallback
            self.stdout.write(
                self.style.WARNING(
                    f'Using default password. Please change it after login!'
                )
            )

        try:
            # Create the admin user
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Admin user "{username}" created successfully!'
                )
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Password: {"*" * len(password)}')
            self.stdout.write('')
            self.stdout.write('🚀 You can now login to the admin panel:')
            self.stdout.write('   Local: http://127.0.0.1:8000/admin/')
            self.stdout.write('   Railway: https://beat-production-5003.up.railway.app/admin/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user: {str(e)}')
            )