from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class WifiPlan(models.Model):
    """WiFi data plans available for purchase"""
    PLAN_TYPES = [
        ('time', 'Time-based'),
        ('data', 'Data-based'),
        ('unlimited', 'Unlimited'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='time')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Time-based plan attributes
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in minutes")
    
    # Data-based plan attributes
    data_limit_mb = models.PositiveIntegerField(null=True, blank=True, help_text="Data limit in MB")
    
    # Bandwidth limits
    upload_speed_kbps = models.PositiveIntegerField(help_text="Upload speed in Kbps")
    download_speed_kbps = models.PositiveIntegerField(help_text="Download speed in Kbps")
    
    # Plan status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
        verbose_name = 'WiFi Plan'
        verbose_name_plural = 'WiFi Plans'
    
    def __str__(self):
        return f"{self.name} - KES {self.price}"
    
    @property
    def duration_display(self):
        if self.duration_minutes:
            hours = self.duration_minutes // 60
            minutes = self.duration_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            return f"{minutes}m"
        return "Unlimited"


class WifiUser(models.Model):
    """WiFi users who purchase internet access"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('disabled', 'Disabled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True)
    mac_address = models.CharField(max_length=17, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # Plan information
    current_plan = models.ForeignKey(WifiPlan, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Usage tracking
    data_used_mb = models.PositiveIntegerField(default=0)
    time_used_minutes = models.PositiveIntegerField(default=0)
    
    # Session timing
    plan_started_at = models.DateTimeField(null=True, blank=True)
    plan_expires_at = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # MikroTik integration
    mikrotik_username = models.CharField(max_length=50, unique=True, blank=True)
    mikrotik_password = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WiFi User'
        verbose_name_plural = 'WiFi Users'
    
    def __str__(self):
        return f"{self.phone_number} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.mikrotik_username:
            # Generate unique MikroTik username
            self.mikrotik_username = f"user_{self.phone_number[-8:]}"
        if not self.mikrotik_password:
            # Generate simple password
            self.mikrotik_password = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'active' and self.plan_expires_at and self.plan_expires_at > timezone.now()
    
    @property
    def time_remaining_minutes(self):
        if self.current_plan and self.current_plan.plan_type == 'time' and self.plan_expires_at:
            remaining = (self.plan_expires_at - timezone.now()).total_seconds() / 60
            return max(0, int(remaining))
        return 0
    
    @property
    def data_remaining_mb(self):
        if self.current_plan and self.current_plan.data_limit_mb:
            return max(0, self.current_plan.data_limit_mb - self.data_used_mb)
        return 0


class UserSession(models.Model):
    """Track user internet sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(WifiUser, on_delete=models.CASCADE, related_name='sessions')
    
    # Session details
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Usage data
    bytes_uploaded = models.BigIntegerField(default=0)
    bytes_downloaded = models.BigIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.started_at}"
    
    @property
    def duration_minutes(self):
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds() / 60)
        return int((timezone.now() - self.started_at).total_seconds() / 60)
    
    @property
    def total_bytes(self):
        return self.bytes_uploaded + self.bytes_downloaded
    
    @property
    def total_mb(self):
        return round(self.total_bytes / (1024 * 1024), 2)
