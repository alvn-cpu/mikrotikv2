from django.contrib import admin
from .models import PaymentTransaction, STKPushRequest, PaymentCallback
from django.utils.html import format_html
from django.utils import timezone


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'plan', 'amount', 'payment_method', 'status_display', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'external_transaction_id', 'user__phone_number', 'phone_number']
    # list_editable = ['status']  # Disabled because we use status_display instead
    ordering = ['-created_at']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = [
        ('Transaction Details', {
            'fields': ('transaction_id', 'external_transaction_id', 'status')
        }),
        ('User & Plan', {
            'fields': ('user', 'plan', 'phone_number')
        }),
        ('Payment Information', {
            'fields': ('amount', 'currency', 'payment_method')
        }),
        ('Processing', {
            'fields': ('processed_by', 'failure_reason'),
            'classes': ('collapse',)
        }),
        ('System Data', {
            'fields': ('provider_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    ]
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'completed' and not obj.processed_by:
                obj.processed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(STKPushRequest)
class STKPushRequestAdmin(admin.ModelAdmin):
    list_display = ['checkout_request_id', 'transaction', 'phone_number', 'amount', 'status_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['checkout_request_id', 'merchant_request_id', 'phone_number', 'transaction__transaction_id']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('STK Push Details', {
            'fields': ('transaction', 'checkout_request_id', 'merchant_request_id')
        }),
        ('Payment Info', {
            'fields': ('phone_number', 'amount', 'status')
        }),
        ('Response Data', {
            'fields': ('result_code', 'result_desc'),
        }),
        ('Provider Data', {
            'fields': ('provider_response', 'callback_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def status_display(self, obj):
        colors = {
            'initiated': 'orange',
            'sent': 'blue',
            'accepted': 'green',
            'cancelled': 'gray',
            'timeout': 'red',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'black')
        icon = '✓' if obj.status == 'accepted' else '✗' if obj.status in ['cancelled', 'failed', 'timeout'] else '⏳'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(PaymentCallback)
class PaymentCallbackAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'callback_type', 'processed', 'created_at']
    list_filter = ['callback_type', 'processed', 'created_at']
    search_fields = ['transaction__transaction_id', 'callback_type']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'processed_at']
    
    fieldsets = [
        ('Callback Information', {
            'fields': ('transaction', 'callback_type', 'processed')
        }),
        ('Callback Data', {
            'fields': ('callback_data',)
        }),
        ('Processing', {
            'fields': ('processed_at',),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    ]
    
    def save_model(self, request, obj, form, change):
        if change and 'processed' in form.changed_data and obj.processed:
            obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)
