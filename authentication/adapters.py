from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to redirect to our custom login page"""
    
    def get_login_redirect_url(self, request):
        """Redirect to dashboard after login"""
        return '/dashboard/'
    
    def get_logout_redirect_url(self, request):
        """Redirect to our custom login page after logout"""  
        return '/auth/login/'
        
    def get_email_confirmation_redirect_url(self, request):
        """Redirect after email confirmation"""
        return '/auth/login/'