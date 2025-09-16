from django.db import models
from django.utils import timezone
from billing.models import WifiUser, WifiPlan
from decimal import Decimal
import uuid


class RadiusUser(models.Model):
    """RADIUS users table - compatible with FreeRADIUS radcheck"""
    username = models.CharField(max_length=64, unique=True, db_index=True)
    attribute = models.CharField(max_length=32, default='Cleartext-Password')
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)
    
    # Link to our WiFi user
    wifi_user = models.ForeignKey(WifiUser, on_delete=models.CASCADE, related_name='radius_users')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'radcheck'
        verbose_name = 'RADIUS User'
        verbose_name_plural = 'RADIUS Users'
    
    def __str__(self):
        return f"{self.username} ({self.attribute})"


class RadiusGroup(models.Model):
    """RADIUS groups for different plan types"""
    groupname = models.CharField(max_length=64, unique=True)
    attribute = models.CharField(max_length=32)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)
    
    # Link to our WiFi plan
    wifi_plan = models.ForeignKey(WifiPlan, on_delete=models.CASCADE, related_name='radius_groups')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'radgroupcheck'
        verbose_name = 'RADIUS Group'
        verbose_name_plural = 'RADIUS Groups'
    
    def __str__(self):
        return f"{self.groupname} - {self.attribute}"


class RadiusUserGroup(models.Model):
    """RADIUS user group membership"""
    username = models.CharField(max_length=64, db_index=True)
    groupname = models.CharField(max_length=64)
    priority = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'radusergroup'
        unique_together = ['username', 'groupname']
        verbose_name = 'RADIUS User Group'
        verbose_name_plural = 'RADIUS User Groups'
    
    def __str__(self):
        return f"{self.username} -> {self.groupname}"


class RadiusAccounting(models.Model):
    """RADIUS accounting data - compatible with FreeRADIUS radacct"""
    radacctid = models.AutoField(primary_key=True)
    acctsessionid = models.CharField(max_length=64, db_index=True)
    acctuniqueid = models.CharField(max_length=32, unique=True)
    username = models.CharField(max_length=64, db_index=True)
    groupname = models.CharField(max_length=64, blank=True)
    realm = models.CharField(max_length=64, blank=True)
    nasipaddress = models.GenericIPAddressField()
    nasportid = models.CharField(max_length=15, blank=True)
    nasporttype = models.CharField(max_length=32, blank=True)
    
    acctstarttime = models.DateTimeField(null=True, blank=True)
    acctupdatetime = models.DateTimeField(null=True, blank=True)
    acctstoptime = models.DateTimeField(null=True, blank=True)
    
    acctinterval = models.IntegerField(null=True, blank=True)
    acctsessiontime = models.IntegerField(null=True, blank=True)
    acctauthentic = models.CharField(max_length=32, blank=True)
    connectinfo_start = models.CharField(max_length=50, blank=True)
    connectinfo_stop = models.CharField(max_length=50, blank=True)
    
    # Data usage
    acctinputoctets = models.BigIntegerField(default=0)
    acctoutputoctets = models.BigIntegerField(default=0)
    
    calledstationid = models.CharField(max_length=50, blank=True)
    callingstationid = models.CharField(max_length=50, blank=True)  # MAC address
    
    acctterminatecause = models.CharField(max_length=32, blank=True)
    servicetype = models.CharField(max_length=32, blank=True)
    framedprotocol = models.CharField(max_length=32, blank=True)
    framedipaddress = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'radacct'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['acctsessionid']),
            models.Index(fields=['acctstarttime']),
            models.Index(fields=['acctstoptime']),
            models.Index(fields=['nasipaddress']),
        ]
        verbose_name = 'RADIUS Accounting'
        verbose_name_plural = 'RADIUS Accounting'
    
    def __str__(self):
        return f"{self.username} - {self.acctsessionid}"
    
    @property
    def total_octets(self):
        return self.acctinputoctets + self.acctoutputoctets
    
    @property
    def total_mb(self):
        return round(self.total_octets / (1024 * 1024), 2)
    
    @property
    def session_duration_minutes(self):
        if self.acctsessiontime:
            return round(self.acctsessiontime / 60, 2)
        return 0
    
    @property
    def is_active(self):
        return self.acctstarttime and not self.acctstoptime


class RadiusPostAuth(models.Model):
    """RADIUS post authentication log"""
    username = models.CharField(max_length=64, db_index=True)
    password = models.CharField(max_length=64)
    reply = models.CharField(max_length=32)
    authdate = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'radpostauth'
        verbose_name = 'RADIUS Post Auth'
        verbose_name_plural = 'RADIUS Post Auth'
    
    def __str__(self):
        return f"{self.username} - {self.reply} at {self.authdate}"


class NasClient(models.Model):
    """NAS (Network Access Server) clients - MikroTik routers"""
    nasname = models.CharField(max_length=128, unique=True)
    shortname = models.CharField(max_length=32)
    type = models.CharField(max_length=30, default='other')
    ports = models.IntegerField(default=1812)
    secret = models.CharField(max_length=60)
    server = models.CharField(max_length=64, blank=True)
    community = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'nas'
        verbose_name = 'NAS Client'
        verbose_name_plural = 'NAS Clients'
    
    def __str__(self):
        return f"{self.shortname} ({self.nasname})"


class RadiusReply(models.Model):
    """RADIUS reply attributes for users"""
    username = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=32)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)
    
    class Meta:
        db_table = 'radreply'
        verbose_name = 'RADIUS Reply'
        verbose_name_plural = 'RADIUS Replies'
    
    def __str__(self):
        return f"{self.username} - {self.attribute}"


class RadiusGroupReply(models.Model):
    """RADIUS group reply attributes"""
    groupname = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=32)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)
    
    class Meta:
        db_table = 'radgroupreply'
        verbose_name = 'RADIUS Group Reply'
        verbose_name_plural = 'RADIUS Group Replies'
    
    def __str__(self):
        return f"{self.groupname} - {self.attribute}"
