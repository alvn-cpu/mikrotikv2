from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
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
                # Specify backend explicitly to avoid conflicts
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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
                # Specify backend explicitly to avoid conflicts
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
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


# Google OAuth views
def google_login(request):
    """Redirect to Google OAuth login"""
    return redirect('/accounts/google/login/')


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


@csrf_exempt
def forgot_password(request):
    """Handle forgot password requests"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            email = data.get('email')
        else:
            email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        try:
            # Check if user exists
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            current_site = get_current_site(request)
            reset_url = f"{request.scheme}://{current_site.domain}/auth/reset-password/{uid}/{token}/"
            
            # Email content
            subject = 'WiFi Billing - Password Reset'
            message = render_to_string('authentication/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': 'WiFi Billing System'
            })
            
            # Send email
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=message,
                    fail_silently=False,
                )
                
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': f'Password reset link sent to {email}'
                    })
                else:
                    messages.success(request, f'Password reset link sent to {email}')
                    return redirect('auth:login')
                    
            except Exception as e:
                error_msg = f'Error sending email: {str(e)}'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'message': error_msg})
                else:
                    messages.error(request, error_msg)
                    
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            success_msg = f'If {email} is registered, a password reset link will be sent shortly.'
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': success_msg})
            else:
                messages.success(request, success_msg)
                return redirect('auth:login')
    
    return render(request, 'authentication/forgot_password.html')


def reset_password_confirm(request, uidb64, token):
    """Handle password reset confirmation"""
    try:
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                
                if not password or len(password) < 6:
                    messages.error(request, 'Password must be at least 6 characters long')
                elif password != confirm_password:
                    messages.error(request, 'Passwords do not match')
                else:
                    user.set_password(password)
                    user.save()
                    messages.success(request, 'Password reset successful! You can now login.')
                    return redirect('auth:login')
            
            return render(request, 'authentication/reset_password.html', {
                'uidb64': uidb64,
                'token': token,
                'user': user
            })
        else:
            messages.error(request, 'Invalid or expired reset link')
            return redirect('auth:login')
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid reset link')
        return redirect('auth:login')
