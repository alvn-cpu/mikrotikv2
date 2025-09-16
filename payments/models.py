from django.db import models
from django.utils import timezone
from billing.models import WifiUser, WifiPlan
import uuid


class PaymentTransaction(models.Model):
    """Track payment transactions for WiFi plans"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('kcb_buni', 'KCB Buni'),
        ('cash', 'Cash'),
        ('admin', 'Admin Credit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, unique=True)
    external_transaction_id = models.CharField(max_length=100, blank=True, help_text="Payment provider transaction ID")
    
    # User and plan information
    user = models.ForeignKey(WifiUser, on_delete=models.CASCADE, related_name='transactions')
    plan = models.ForeignKey(WifiPlan, on_delete=models.CASCADE)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='kcb_buni')
    
    # Phone number for payment
    phone_number = models.CharField(max_length=15)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Payment provider response data
    provider_response = models.JSONField(blank=True, null=True)
    failure_reason = models.TextField(blank=True)
    
    # Admin fields
    processed_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Admin user who processed this transaction"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.phone_number} - KES {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.transaction_id = f"TXN{timestamp}{str(uuid.uuid4())[:8].upper()}"
        
        # Set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def can_retry(self):
        return self.status in ['failed', 'cancelled']


class STKPushRequest(models.Model):
    """Track STK Push requests for M-Pesa payments"""
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('sent', 'Sent to Phone'),
        ('accepted', 'User Accepted'),
        ('cancelled', 'User Cancelled'),
        ('timeout', 'Timeout'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='stk_request')
    
    # STK Push details
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Provider response data
    provider_response = models.JSONField(blank=True, null=True)
    callback_response = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'STK Push Request'
        verbose_name_plural = 'STK Push Requests'
    
    def __str__(self):
        return f"STK-{self.checkout_request_id} - {self.phone_number}"
    
    @property
    def is_successful(self):
        return self.status == 'accepted' and self.result_code == '0'


class PaymentCallback(models.Model):
    """Store payment provider callback data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='callbacks')
    
    # Callback details
    callback_type = models.CharField(max_length=50)  # 'confirmation', 'validation', etc.
    callback_data = models.JSONField()
    
    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Callback'
        verbose_name_plural = 'Payment Callbacks'
    
    def __str__(self):
        return f"{self.callback_type} - {self.transaction.transaction_id}"
