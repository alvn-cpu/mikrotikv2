"""
URL configuration for wifi_billing_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from debug_views import health_check, debug_info
from create_admin_view import create_admin_user
from fix_admin_web import fix_admin_permissions

# Simple favicon handler
def favicon_view(request):
    return HttpResponse(status=204)  # No Content

# Admin redirect handler - redirects all admin URLs to signin
def admin_redirect(request, path=None):
    """Redirect admin URLs to custom login with next parameter"""
    return redirect('/auth/login/?next=' + request.get_full_path())


urlpatterns = [
    # Redirect all admin URLs to custom signin
    path('admin/', admin_redirect, name='admin_redirect'),
    path('admin/<path:path>', admin_redirect, name='admin_redirect_all'),
    path('dashboard/', include('dashboard.urls')),
    path('mikrotik/', include('mikrotik_integration.urls')),
    path('auth/', include('authentication.urls')),
    path('admin-login/', lambda request: redirect('/auth/login/'), name='admin_login'),
    path('accounts/', include('allauth.urls')),  # Allauth URLs for OAuth
    path('payments/', include('payments.urls')),
    path('payments/', include('payments.webhook_urls')),
    # Main billing URLs (captive portal) - handle these at root level
    path('', include('billing.urls')),
    # Temporary debug endpoints
    path('health/', health_check, name='health_check'),
    path('debug/', debug_info, name='debug_info'),
    path('fix-admin-permissions/', fix_admin_permissions, name='fix_admin_permissions'),
    # Favicon handler to prevent 400 errors
    path('favicon.ico', favicon_view, name='favicon'),
]
