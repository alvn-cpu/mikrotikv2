from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'dashboard'

def dashboard_redirect(request):
    return redirect('dashboard:admin_dashboard')

urlpatterns = [
    path('', dashboard_redirect, name='dashboard_index'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Plan management endpoints (AJAX/POST JSON)
    path('plans/create/', views.create_plan, name='create_plan'),
    path('plans/<uuid:plan_id>/get/', views.get_plan, name='get_plan'),
    path('plans/<uuid:plan_id>/update/', views.update_plan, name='update_plan'),
    path('plans/<uuid:plan_id>/delete/', views.delete_plan, name='delete_plan'),
    
    # Station management endpoints
    path('stations/create/', views.create_station, name='create_station'),
    path('stations/<int:station_id>/get/', views.get_station, name='get_station'),
    path('stations/<int:station_id>/update/', views.update_station, name='update_station'),
    path('stations/<int:station_id>/delete/', views.delete_station, name='delete_station'),
    
    # Station configuration downloads
    path('stations/<int:station_id>/config/', views.download_station_config, name='download_station_config'),  # Complete ZIP package
    path('stations/<int:station_id>/config-file/', views.download_station_config_file, name='download_station_config_file'),  # .rsc only
    path('stations/<int:station_id>/login-page/', views.download_station_login_page, name='download_station_login_page'),  # .html only
    
    path('stations/<int:station_id>/test-payment/', views.test_payment_credentials, name='test_payment_credentials'),
    
    # Data endpoints for new sections
    path('api/users/', views.get_users_data, name='get_users_data'),
    path('api/transactions/', views.get_transactions_data, name='get_transactions_data'),
    path('api/sessions/', views.get_sessions_data, name='get_sessions_data'),
    path('export/transactions/', views.export_transactions_csv, name='export_transactions_csv'),
]
