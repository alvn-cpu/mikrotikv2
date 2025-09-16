"""
Debug views for Railway deployment troubleshooting
Add this to your main urls.py temporarily to debug issues
"""

from django.http import JsonResponse, HttpResponse
from django.conf import settings
import os

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'OK',
        'message': 'WiFi Billing System is running!',
        'host': request.get_host(),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database': 'PostgreSQL' if 'postgresql' in settings.DATABASES['default']['ENGINE'] else 'SQLite'
    })

def debug_info(request):
    """Debug information (remove in production)"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Debug mode disabled'})
    
    return JsonResponse({
        'settings': {
            'DEBUG': settings.DEBUG,
            'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
            'DATABASE_ENGINE': settings.DATABASES['default']['ENGINE'],
            'SITE_URL': getattr(settings, 'SITE_URL', 'Not set'),
            'STATIC_URL': settings.STATIC_URL,
        },
        'environment': {
            'DATABASE_URL': os.environ.get('DATABASE_URL', 'Not set')[:50] + '...' if os.environ.get('DATABASE_URL') else 'Not set',
            'SECRET_KEY': 'Set' if os.environ.get('SECRET_KEY') else 'Not set',
            'DEBUG': os.environ.get('DEBUG', 'Not set'),
            'ALLOWED_HOSTS': os.environ.get('ALLOWED_HOSTS', 'Not set'),
        },
        'request': {
            'host': request.get_host(),
            'path': request.path,
            'method': request.method,
            'secure': request.is_secure(),
        }
    })

# Add this to your main urls.py temporarily:
# from debug_views import health_check, debug_info
# 
# urlpatterns = [
#     path('health/', health_check, name='health_check'),
#     path('debug/', debug_info, name='debug_info'),
#     # ... your other urls
# ]