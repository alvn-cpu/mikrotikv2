from django.contrib import admin
from .models import RouterConfig, UserProfile, ActiveUser, RouterCommand
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from .services import MikroTikManager, MikroTikAPIError


@admin.register(RouterConfig)
class RouterConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'api_port', 'username', 'connection_status_display', 'is_active', 'last_connected']
    list_filter = ['is_active', 'connection_status', 'created_at']
    search_fields = ['name', 'host', 'username']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = [
        ('Router Information', {
            'fields': ('name', 'host', 'api_port', 'username', 'password')
        }),
        ('Settings', {
            'fields': ('hotspot_interface', 'address_pool', 'is_active')
        }),
        ('Connection Status', {
            'fields': ('connection_status', 'last_connected'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def connection_status_display(self, obj):
        colors = {
            'connected': 'green',
            'disconnected': 'red',
            'error': 'orange',
            'unknown': 'gray'
        }
        color = colors.get(obj.connection_status, 'black')
        icon = '✓' if obj.connection_status == 'connected' else '✗' if obj.connection_status == 'disconnected' else '?'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.connection_status.title()
        )
    connection_status_display.short_description = 'Connection Status'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'speed_display', 'session_timeout', 'idle_timeout', 'shared_users', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = [
        ('Profile Information', {
            'fields': ('name', 'is_active')
        }),
        ('Bandwidth Limits', {
            'fields': ('download_limit', 'upload_limit')
        }),
        ('Session Settings', {
            'fields': ('session_timeout', 'idle_timeout', 'shared_users')
        })
    ]
    
    def speed_display(self, obj):
        return f"{obj.download_limit}↓/{obj.upload_limit}↑"
    speed_display.short_description = 'Speed (D/U)'


@admin.register(ActiveUser)
class ActiveUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'wifi_user', 'ip_address', 'router', 'login_time', 'uptime', 'data_usage_display', 'is_active']
    list_filter = ['is_active', 'router', 'login_time']
    search_fields = ['username', 'ip_address', 'mac_address', 'wifi_user__phone_number']
    ordering = ['-login_time']
    readonly_fields = ['id', 'created_at', 'last_updated', 'total_bytes', 'total_mb']
    
    fieldsets = [
        ('User Information', {
            'fields': ('wifi_user', 'router', 'username', 'is_active')
        }),
        ('Session Details', {
            'fields': ('mikrotik_session_id', 'ip_address', 'mac_address', 'login_time', 'uptime')
        }),
        ('Usage Statistics', {
            'fields': ('bytes_in', 'bytes_out', 'total_bytes', 'total_mb', 'packets_in', 'packets_out')
        }),
        ('System Fields', {
            'fields': ('id', 'created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    ]
    
    def data_usage_display(self, obj):
        return f"{obj.total_mb} MB"
    data_usage_display.short_description = 'Data Usage'


@admin.register(RouterCommand)
class RouterCommandAdmin(admin.ModelAdmin):
    list_display = ['command_type', 'router', 'wifi_user', 'success_display', 'executed_at']
    list_filter = ['command_type', 'success', 'router', 'executed_at']
    search_fields = ['wifi_user__phone_number', 'error_message']
    ordering = ['-executed_at']
    readonly_fields = ['id', 'executed_at']
    
    fieldsets = [
        ('Command Information', {
            'fields': ('command_type', 'router', 'wifi_user')
        }),
        ('Execution Details', {
            'fields': ('success', 'executed_at')
        }),
        ('Command Data', {
            'fields': ('command_data',),
            'classes': ('collapse',)
        }),
        ('Response Data', {
            'fields': ('response_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    ]
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green; font-weight: bold;">✓ Success</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Failed</span>')
    success_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        # Prevent manual creation of router commands through admin
        return False
