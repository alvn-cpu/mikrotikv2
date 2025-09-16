from django.db import models
from billing.models import WifiUser
from django.utils import timezone
import uuid


class RouterConfig(models.Model):
    """MikroTik router configuration"""
    name = models.CharField(max_length=100, unique=True)
    host = models.CharField(max_length=100, help_text="Router IP address")
    api_port = models.IntegerField(default=8728)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    
    # Router settings
    is_active = models.BooleanField(default=True)
    hotspot_interface = models.CharField(max_length=50, default='wlan1')
    address_pool = models.CharField(max_length=50, default='dhcp_pool1')
    
    # KCB Payment Integration (Station-specific account details)
    business_name = models.CharField(max_length=100, blank=True, help_text="Business name for this station")
    
    # KCB Account Details (what station owner provides)
    kcb_account_type = models.CharField(max_length=20, choices=[
        ('paybill', 'Paybill Number'),
        ('till', 'Till Number'),
        ('bank', 'Bank Account')
    ], default='paybill', help_text="Type of KCB account")
    
    # Legacy payment method field (for backward compatibility)
    payment_method = models.CharField(max_length=20, choices=[
        ('paybill', 'Paybill'),
        ('till', 'Till Number'),
        ('account', 'Bank Account')
    ], default='paybill', blank=True, help_text="Payment method (legacy)")
    
    # Legacy fields for compatibility with existing views
    paybill_number = models.CharField(max_length=50, blank=True, help_text="Legacy paybill number field")
    account_number = models.CharField(max_length=50, blank=True, help_text="Legacy account number field")
    till_number = models.CharField(max_length=50, blank=True, help_text="Legacy till number field")
    
    kcb_account_number = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="KCB Paybill Number or Bank Account Number"
    )
    
    account_name = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Account holder name (for reference)"
    )
    
    # Payment settings
    enable_payments = models.BooleanField(default=True, help_text="Enable payments for this station")
    
    # Connection status
    last_connected = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(max_length=20, default='unknown')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Router Configuration'
        verbose_name_plural = 'Router Configurations'
    
    def __str__(self):
        return f"{self.name} - {self.host}"


class UserProfile(models.Model):
    """MikroTik user profile for bandwidth management"""
    name = models.CharField(max_length=50, unique=True)
    
    # Bandwidth limits
    download_limit = models.CharField(max_length=20, help_text="e.g., 1M, 512k")
    upload_limit = models.CharField(max_length=20, help_text="e.g., 256k, 128k")
    
    # Session limits
    session_timeout = models.CharField(max_length=20, blank=True, help_text="e.g., 1h, 30m")
    idle_timeout = models.CharField(max_length=20, blank=True, help_text="e.g., 5m")
    
    # Additional settings
    shared_users = models.IntegerField(default=1, help_text="Number of simultaneous sessions")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.name} ({self.download_limit}/{self.upload_limit})"


class ActiveUser(models.Model):
    """Track active users on MikroTik router"""
    wifi_user = models.ForeignKey(WifiUser, on_delete=models.CASCADE, related_name='active_sessions')
    router = models.ForeignKey(RouterConfig, on_delete=models.CASCADE)
    
    # MikroTik session details
    mikrotik_session_id = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17)
    
    # Session info
    login_time = models.DateTimeField()
    uptime = models.CharField(max_length=20, blank=True)
    
    # Usage statistics
    bytes_in = models.BigIntegerField(default=0)
    bytes_out = models.BigIntegerField(default=0)
    packets_in = models.BigIntegerField(default=0)
    packets_out = models.BigIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['wifi_user', 'router', 'mikrotik_session_id']
        verbose_name = 'Active User'
        verbose_name_plural = 'Active Users'
    
    def __str__(self):
        return f"{self.username} - {self.ip_address}"
    
    @property
    def total_bytes(self):
        return self.bytes_in + self.bytes_out
    
    @property
    def total_mb(self):
        return round(self.total_bytes / (1024 * 1024), 2)


class RouterCommand(models.Model):
    """Log MikroTik API commands"""
    COMMAND_TYPES = [
        ('create_user', 'Create User'),
        ('delete_user', 'Delete User'),
        ('enable_user', 'Enable User'),
        ('disable_user', 'Disable User'),
        ('get_active_users', 'Get Active Users'),
        ('disconnect_user', 'Disconnect User'),
        ('update_profile', 'Update Profile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    router = models.ForeignKey(RouterConfig, on_delete=models.CASCADE, related_name='commands')
    wifi_user = models.ForeignKey(WifiUser, on_delete=models.CASCADE, null=True, blank=True)
    
    command_type = models.CharField(max_length=30, choices=COMMAND_TYPES)
    command_data = models.JSONField()
    
    # Execution details
    executed_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Router Command'
        verbose_name_plural = 'Router Commands'
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.command_type} - {self.router.name}"
