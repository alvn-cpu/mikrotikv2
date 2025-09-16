"""
Custom authentication decorators for WiFi Billing System
Replaces Django admin decorators since admin is disabled
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """
    Custom decorator to require admin/staff access for dashboard
    Replaces @staff_member_required since Django admin is disabled
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access the admin dashboard.')
            return redirect('/auth/login/?next=' + request.get_full_path())
        
        # Allow all authenticated users for now - you can add more restrictions here
        # For example, check for is_staff or specific permissions:
        # if not request.user.is_staff:
        #     messages.error(request, 'You do not have permission to access this area.')
        #     return redirect('/auth/login/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(view_func):
    """
    Decorator that requires superuser access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this area.')
            return redirect('/auth/login/?next=' + request.get_full_path())
        
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access this area.')
            return redirect('/dashboard/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def staff_required(view_func):
    """
    Decorator that requires staff access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this area.')
            return redirect('/auth/login/?next=' + request.get_full_path())
        
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this area.')
            return redirect('/dashboard/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper