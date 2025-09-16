from django.urls import path
from . import views

app_name = 'mikrotik_integration'

urlpatterns = [
    # API endpoints for real-time monitoring
    path('api/router-status/', views.router_status_api, name='router_status_api'),
    path('api/active-sessions/', views.active_sessions_api, name='active_sessions_api'),
    path('api/session-statistics/', views.session_statistics_api, name='session_statistics_api'),
    path('api/disconnect-user/', views.disconnect_user_api, name='disconnect_user_api'),
    path('api/sync-sessions/', views.sync_sessions_api, name='sync_sessions_api'),
]