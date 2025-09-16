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
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from debug_views import health_check, debug_info
from create_admin_view import create_admin_user

# Simple favicon handler
def favicon_view(request):
    return HttpResponse(status=204)  # No Content


urlpatterns = [
    path('admin/', admin.site.urls),
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
    # Favicon handler to prevent 400 errors
    path('favicon.ico', favicon_view, name='favicon'),
]
