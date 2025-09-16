from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import os


def create_admin_user(request):
    """Create admin user via web request - REMOVE AFTER USE!"""
    
    # Security check - only allow in debug mode or with special parameter
    if not request.GET.get('create_admin_secret') == 'railway_admin_2025':
        return JsonResponse({
            'error': 'Access denied. Use ?create_admin_secret=railway_admin_2025'
        }, status=403)
    
    try:
        # Check if admin already exists
        if User.objects.filter(username='admin').exists():
            return JsonResponse({
                'status': 'warning',
                'message': 'Admin user already exists!',
                'existing_users': list(User.objects.filter(is_superuser=True).values_list('username', flat=True))
            })
        
        # Create admin user
        admin_password = 'railway_admin_2025'  # You'll change this after login
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@railway.app',
            password=admin_password
        )
        
        return JsonResponse({
            'status': 'success',
            'message': '✅ Admin user created successfully!',
            'username': 'admin',
            'password': admin_password,
            'admin_url': 'https://beat-production-5003.up.railway.app/admin/',
            'note': '⚠️ IMPORTANT: Change this password after login!',
            'login_instructions': [
                '1. Go to https://beat-production-5003.up.railway.app/admin/',
                '2. Login with username: admin, password: railway_admin_2025',
                '3. Change password immediately in admin panel',
                '4. Remove this create-admin URL from your code'
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create admin user: {str(e)}'
        }, status=500)