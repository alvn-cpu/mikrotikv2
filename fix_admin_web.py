#!/usr/bin/env python3
"""
Web endpoint to fix admin permissions
Visit: https://beat-production-5003.up.railway.app/fix-admin-permissions/
"""

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os

@csrf_exempt
@require_http_methods(["GET", "POST"])
def fix_admin_permissions(request):
    """Fix admin user permissions via web interface"""
    
    # Security check - only allow in debug mode or with specific token
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    admin_token = request.GET.get('token') or request.POST.get('token')
    expected_token = os.environ.get('ADMIN_FIX_TOKEN', 'broadcom2024')
    
    if not debug_mode and admin_token != expected_token:
        return JsonResponse({
            'error': 'Access denied. Provide valid token parameter.',
            'usage': 'Add ?token=your_token to the URL'
        }, status=403)
    
    try:
        username = request.GET.get('username') or request.POST.get('username') or 'admin'
        new_password = request.GET.get('password') or request.POST.get('password')
        
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
            action = 'Created new superuser'
        else:
            # Update existing user permissions
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            
            if new_password:
                user.set_password(new_password)
                action = 'Updated permissions and password'
            else:
                action = 'Updated permissions (password unchanged)'
            
            user.save()
        
        # Get all users for display
        all_users = []
        for u in User.objects.all().order_by('-is_superuser', '-is_staff', 'username'):
            all_users.append({
                'username': u.username,
                'email': u.email or 'No email',
                'is_active': u.is_active,
                'is_staff': u.is_staff,
                'is_superuser': u.is_superuser,
                'can_access_admin': u.is_staff,
                'last_login': str(u.last_login) if u.last_login else 'Never',
                'date_joined': str(u.date_joined)
            })
        
        if request.content_type == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({
                'success': True,
                'action': action,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'can_access_admin': user.is_staff
                },
                'all_users': all_users
            })
        else:
            # Return HTML response
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin Permissions Fixed - BROADCOM NETWORKS</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
                    .success {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .user-card {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .admin-badge {{ background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
                    .staff-badge {{ background: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
                    .user-badge {{ background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
                    .links {{ margin-top: 30px; }}
                    .links a {{ display: inline-block; margin: 5px 10px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                    .links a:hover {{ background: #0056b3; }}
                    .form {{ background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .form input {{ width: 200px; padding: 8px; margin: 5px; border: 1px solid #ccc; border-radius: 3px; }}
                    .form button {{ background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 3px; cursor: pointer; }}
                </style>
            </head>
            <body>
                <h1>🔧 BROADCOM NETWORKS - Admin Permissions Manager</h1>
                
                <div class="success">
                    <strong>✅ {action}</strong><br>
                    User <strong>{user.username}</strong> can now access the Django admin panel.
                </div>
                
                <div class="info">
                    <strong>📋 Current User Status:</strong><br>
                    Username: {user.username}<br>
                    Email: {user.email}<br>
                    Is Active: {'✅' if user.is_active else '❌'}<br>
                    Is Staff: {'✅' if user.is_staff else '❌'}<br>
                    Is Superuser: {'✅' if user.is_superuser else '❌'}<br>
                    Can Access Admin: {'✅ YES' if user.is_staff else '❌ NO'}
                </div>
                
                <h2>👥 All Users in System</h2>
            """
            
            for u in all_users:
                badge = '👑 SUPERUSER' if u['is_superuser'] else ('👨‍💼 STAFF' if u['is_staff'] else '👤 USER')
                access = '✅ YES' if u['can_access_admin'] else '❌ NO'
                
                html += f"""
                <div class="user-card">
                    <strong>{u['username']}</strong> ({u['email']}) 
                    <span class="{'admin-badge' if u['is_superuser'] else 'staff-badge' if u['is_staff'] else 'user-badge'}">{badge}</span><br>
                    <small>Can Access Admin: {access} | Last Login: {u['last_login']}</small>
                </div>
                """
            
            html += f"""
                <div class="form">
                    <h3>🔧 Fix Another User</h3>
                    <form method="post">
                        <input type="text" name="username" placeholder="Username" value="admin">
                        <input type="password" name="password" placeholder="New Password (optional)">
                        <input type="hidden" name="token" value="{admin_token or expected_token}">
                        <button type="submit">Fix Permissions</button>
                    </form>
                </div>
                
                <div class="links">
                    <h3>🔗 Quick Access Links</h3>
                    <a href="/admin/" target="_blank">Django Admin Panel</a>
                    <a href="/auth/login/" target="_blank">Custom Login Page</a>
                    <a href="/dashboard/" target="_blank">Dashboard</a>
                    <a href="?format=json&token={admin_token or expected_token}" target="_blank">JSON Response</a>
                </div>
            </body>
            </html>
            """
            
            return HttpResponse(html)
    
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'details': 'Failed to fix admin permissions'
        }
        
        if request.content_type == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse(error_response, status=500)
        else:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error - BROADCOM NETWORKS</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                    .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>❌ Error</h1>
                <div class="error">
                    <strong>Failed to fix admin permissions:</strong><br>
                    {str(e)}
                </div>
                <p><a href="javascript:history.back()">← Go Back</a></p>
            </body>
            </html>
            """
            return HttpResponse(html, status=500)