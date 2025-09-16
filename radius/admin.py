from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.utils import timezone
from .models import (
    RadiusUser, RadiusGroup, RadiusUserGroup, RadiusAccounting,
    RadiusPostAuth, NasClient, RadiusReply, RadiusGroupReply
)


@admin.register(RadiusUser)
class RadiusUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'wifi_user', 'attribute', 'created_at']
    list_filter = ['attribute', 'created_at']
    search_fields = ['username', 'wifi_user__phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wifi_user')


@admin.register(RadiusGroup)
class RadiusGroupAdmin(admin.ModelAdmin):
    list_display = ['groupname', 'wifi_plan', 'attribute', 'value', 'created_at']
    list_filter = ['attribute', 'wifi_plan', 'created_at']
    search_fields = ['groupname', 'wifi_plan__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wifi_plan')


@admin.register(RadiusUserGroup)
class RadiusUserGroupAdmin(admin.ModelAdmin):
    list_display = ['username', 'groupname', 'priority']
    list_filter = ['groupname', 'priority']
    search_fields = ['username', 'groupname']


@admin.register(RadiusAccounting)
class RadiusAccountingAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'acctsessionid', 'nasipaddress', 
        'session_status', 'session_duration_display', 
        'data_usage_display', 'acctstarttime'
    ]
    list_filter = [
        'acctstarttime', 'acctstoptime', 'nasipaddress',
        'acctterminatecause'
    ]
    search_fields = ['username', 'acctsessionid', 'callingstationid']
    readonly_fields = [
        'radacctid', 'total_octets', 'total_mb', 
        'session_duration_minutes', 'is_active'
    ]
    ordering = ['-acctstarttime']
    
    def session_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span class="badge" style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px;">Active</span>'
            )
        else:
            return format_html(
                '<span class="badge" style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px;">Ended</span>'
            )
    session_status.short_description = 'Status'
    
    def session_duration_display(self, obj):
        minutes = obj.session_duration_minutes
        if minutes > 60:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"
        return f"{minutes:.0f}m"
    session_duration_display.short_description = 'Duration'
    
    def data_usage_display(self, obj):
        mb = obj.total_mb
        if mb > 1024:
            gb = mb / 1024
            return f"{gb:.2f} GB"
        return f"{mb:.1f} MB"
    data_usage_display.short_description = 'Data Usage'
    
    fieldsets = [
        ('Session Info', {
            'fields': ('username', 'acctsessionid', 'acctuniqueid')
        }),
        ('Network Details', {
            'fields': ('nasipaddress', 'framedipaddress', 'callingstationid', 'calledstationid')
        }),
        ('Timing', {
            'fields': ('acctstarttime', 'acctupdatetime', 'acctstoptime', 'session_duration_minutes')
        }),
        ('Data Usage', {
            'fields': ('acctinputoctets', 'acctoutputoctets', 'total_octets', 'total_mb')
        }),
        ('Connection Info', {
            'fields': ('acctterminatecause', 'connectinfo_start', 'connectinfo_stop'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('radacctid', 'is_active'),
            'classes': ('collapse',)
        })
    ]


@admin.register(RadiusPostAuth)
class RadiusPostAuthAdmin(admin.ModelAdmin):
    list_display = ['username', 'reply', 'authdate']
    list_filter = ['reply', 'authdate']
    search_fields = ['username']
    ordering = ['-authdate']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NasClient)
class NasClientAdmin(admin.ModelAdmin):
    list_display = ['shortname', 'nasname', 'type', 'ports', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['shortname', 'nasname', 'description']
    list_editable = ['is_active']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('shortname', 'nasname', 'description', 'is_active')
        }),
        ('Network Configuration', {
            'fields': ('type', 'ports', 'secret', 'server', 'community')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RadiusReply)
class RadiusReplyAdmin(admin.ModelAdmin):
    list_display = ['username', 'attribute', 'op', 'value']
    list_filter = ['attribute']
    search_fields = ['username', 'attribute']


@admin.register(RadiusGroupReply)
class RadiusGroupReplyAdmin(admin.ModelAdmin):
    list_display = ['groupname', 'attribute', 'op', 'value']
    list_filter = ['groupname', 'attribute']
    search_fields = ['groupname', 'attribute']
