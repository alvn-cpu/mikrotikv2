from django.contrib import admin
from .models import WifiPlan, WifiUser, UserSession
from django.utils.html import format_html
from django.utils import timezone


@admin.register(WifiPlan)
class WifiPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_display', 'data_limit_display', 'speed_display', 'is_active', 'created_at']
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['price']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'description', 'plan_type', 'price', 'is_active')
        }),
        ('Plan Limits', {
            'fields': ('duration_minutes', 'data_limit_mb'),
            'description': 'Set duration for time-based plans or data limit for data-based plans'
        }),
        ('Bandwidth Settings', {
            'fields': ('download_speed_kbps', 'upload_speed_kbps')
        }),
    ]
    
    def duration_display(self, obj):
        return obj.duration_display
    duration_display.short_description = 'Duration'
    
    def data_limit_display(self, obj):
        if obj.data_limit_mb:
            return f"{obj.data_limit_mb} MB"
        return "Unlimited"
    data_limit_display.short_description = 'Data Limit'
    
    def speed_display(self, obj):
        return f"{obj.download_speed_kbps}↓/{obj.upload_speed_kbps}↑ Kbps"
    speed_display.short_description = 'Speed (D/U)'


@admin.register(WifiUser)
class WifiUserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'status', 'current_plan', 'plan_expires_at', 'data_used_display', 'mikrotik_username', 'created_at']
    list_filter = ['status', 'current_plan', 'created_at']
    search_fields = ['phone_number', 'mikrotik_username', 'mac_address']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['mikrotik_username', 'mikrotik_password', 'id']
    
    fieldsets = [
        ('User Information', {
            'fields': ('phone_number', 'mac_address', 'ip_address')
        }),
        ('Plan Information', {
            'fields': ('current_plan', 'status', 'plan_started_at', 'plan_expires_at')
        }),
        ('Usage Statistics', {
            'fields': ('data_used_mb', 'time_used_minutes'),
            'classes': ('collapse',)
        }),
        ('MikroTik Integration', {
            'fields': ('mikrotik_username', 'mikrotik_password'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def data_used_display(self, obj):
        if obj.current_plan and obj.current_plan.data_limit_mb:
            percentage = (obj.data_used_mb / obj.current_plan.data_limit_mb) * 100
            color = 'red' if percentage > 90 else 'orange' if percentage > 75 else 'green'
            return format_html(
                '<span style="color: {}">{} MB ({:.1f}%)</span>',
                color, obj.data_used_mb, percentage
            )
        return f"{obj.data_used_mb} MB"
    data_used_display.short_description = 'Data Used'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'ip_address', 'started_at', 'duration_display', 'data_usage_display', 'is_active']
    list_filter = ['is_active', 'started_at']
    search_fields = ['user__phone_number', 'session_id', 'ip_address', 'mac_address']
    ordering = ['-started_at']
    readonly_fields = ['id', 'total_bytes', 'total_mb', 'duration_minutes']
    
    fieldsets = [
        ('Session Information', {
            'fields': ('user', 'session_id', 'ip_address', 'mac_address', 'is_active')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration_minutes')
        }),
        ('Usage Statistics', {
            'fields': ('bytes_uploaded', 'bytes_downloaded', 'total_bytes', 'total_mb')
        }),
        ('System Fields', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    ]
    
    def duration_display(self, obj):
        duration = obj.duration_minutes
        hours = duration // 60
        minutes = duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    duration_display.short_description = 'Duration'
    
    def data_usage_display(self, obj):
        return f"{obj.total_mb} MB"
    data_usage_display.short_description = 'Data Usage'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and obj.ended_at:  # session is ended
            readonly_fields.extend(['started_at', 'ended_at', 'bytes_uploaded', 'bytes_downloaded'])
        return readonly_fields
