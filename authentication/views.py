from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


def custom_login(request):
    """Custom login page with modern design"""
    if request.user.is_authenticated:
        return redirect('dashboard:admin_dashboard')
    
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # Handle AJAX login
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            # Handle form login
            username = request.POST.get('username')
            password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful!',
                        'redirect_url': '/dashboard/'
                    })
                messages.success(request, 'Welcome back!')
                return redirect('dashboard:admin_dashboard')
            else:
                error_msg = 'Invalid username or password'
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                messages.error(request, error_msg)
    
    return render(request, 'authentication/login.html')


def custom_signup(request):
    """Custom signup page"""
    if request.user.is_authenticated:
        return redirect('dashboard:admin_dashboard')
    
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            for error in errors:
                messages.error(request, error)
        else:
            # Create user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                login(request, user)
                
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': 'Account created successfully!',
                        'redirect_url': '/dashboard/'
                    })
                messages.success(request, 'Account created successfully!')
                return redirect('dashboard:admin_dashboard')
            except Exception as e:
                error_msg = f'Error creating account: {str(e)}'
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                messages.error(request, error_msg)
    
    return render(request, 'authentication/signup.html')


def custom_logout(request):
    """Custom logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('auth:login')


# Google OAuth views (placeholder for future implementation)
def google_login(request):
    """Google OAuth login - placeholder"""
    messages.info(request, 'Google login will be available soon!')
    return redirect('auth:login')


@csrf_exempt
def check_username(request):
    """AJAX endpoint to check if username is available"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({'available': False, 'message': 'Username required'})
        
        if len(username) < 3:
            return JsonResponse({'available': False, 'message': 'Username too short'})
        
        available = not User.objects.filter(username=username).exists()
        return JsonResponse({
            'available': available,
            'message': 'Username available' if available else 'Username already taken'
        })
    
    return JsonResponse({'error': 'Invalid request method'})