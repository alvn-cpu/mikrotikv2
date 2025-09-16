import logging
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Custom error handling middleware for authentication errors"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle exceptions and provide better error messages"""
        
        # Log the exception
        logger.error(f"Exception in {request.path}: {str(exception)}", exc_info=True)
        
        # If it's an authentication-related request, provide specific error handling
        if request.path.startswith('/auth/') or request.path.startswith('/accounts/'):
            
            # Check if it's an AJAX request
            if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred during authentication. Please try again.',
                    'error_type': 'authentication_error'
                }, status=500)
            
            # For regular requests, render a nice error page
            context = {
                'error_message': 'Authentication Error',
                'error_description': 'There was an issue with the authentication system. Please try again or contact support.',
                'site_name': 'BROADCOM NETWORKS'
            }
            
            if settings.DEBUG:
                context['debug_info'] = str(exception)
            
            return render(request, 'authentication/error.html', context, status=500)
        
        # Let Django handle other exceptions normally
        return None