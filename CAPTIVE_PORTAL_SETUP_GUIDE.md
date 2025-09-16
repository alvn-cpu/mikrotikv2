# MikroTik Captive Portal Setup Guide for WiFi Billing System

## Overview
This guide shows how to configure your MikroTik routers to redirect users to your Django billing system for plan selection and payment.

## Prerequisites
- MikroTik router with RouterOS
- Django billing system running on accessible server
- RADIUS server (FreeRADIUS) configured
- Network connectivity between MikroTik and Django server

## Step-by-Step Setup

### 1. **Django Server Configuration**

#### A. Update Django Settings
Make sure your Django server is accessible from MikroTik:

```python
# In wifi_billing/settings.py
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'YOUR_SERVER_IP',  # Replace with your actual server IP
    '*',  # For development only - remove in production
]

# Make sure these apps are installed
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # For cross-origin requests
    'billing',
    'payments',
    'radius',
    'dashboard',
    'mikrotik_integration',
]

# Add CORS settings
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]

# Allow cross-origin requests from MikroTik
CORS_ALLOW_ALL_ORIGINS = True  # For development
```

#### B. Start Django Server
```bash
# In your project directory
cd "C:\Users\tech\Desktop\BILLING SYSTEM"
wifi_billing_env\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

### 2. **MikroTik Router Configuration**

#### A. Upload Configuration Script
1. Copy the `mikrotik_hotspot_config.rsc` file
2. Replace `YOUR_SERVER_IP` with your actual Django server IP
3. Upload and run the script in MikroTik RouterOS

#### B. Upload Custom Login Page
1. Copy the `mikrotik_login.html` file
2. Replace `YOUR_DJANGO_SERVER_IP` with your server IP
3. Upload to MikroTik under Files > hotspot directory
4. Rename to `login.html`

### 3. **Network Flow Explanation**

#### How the Captive Portal Works:
```
1. User connects to WiFi
   ↓
2. MikroTik intercepts HTTP requests
   ↓
3. MikroTik shows login.html (custom page)
   ↓
4. User clicks "Get Internet Access"
   ↓
5. Redirects to Django: http://your-server:8000/plans/?mac=XX:XX:XX:XX:XX:XX
   ↓
6. User selects plan and pays
   ↓
7. Django creates RADIUS user
   ↓
8. User gets internet access via RADIUS authentication
```

### 4. **Key URLs in Your Django System**

- **Portal Entry**: `http://your-server:8000/`
- **Plan Selection**: `http://your-server:8000/plans/`
- **Payment Form**: `http://your-server:8000/payment/<plan_id>/`
- **Payment Status**: `http://your-server:8000/payment/status/<transaction_id>/`
- **User Status**: `http://your-server:8000/status/`

### 5. **RADIUS Integration**

#### A. Configure FreeRADIUS clients.conf
```
client mikrotik_main {
    ipaddr = 192.168.1.1
    secret = radius123
    shortname = MainRouter
    nastype = mikrotik
}

client mikrotik_secondary {
    ipaddr = 192.168.1.2
    secret = radius456
    shortname = SecondaryRouter
    nastype = mikrotik
}
```

#### B. Setup RADIUS Database Connection
Point FreeRADIUS to your Django database for user authentication.

### 6. **Testing the Setup**

#### A. Test Django Server
1. Visit `http://your-server-ip:8000/plans/` directly
2. Verify plan selection page loads correctly

#### B. Test MikroTik Hotspot
1. Connect to WiFi network
2. Open browser - should see custom login page
3. Click "Get Internet Access"
4. Should redirect to Django plan selection

#### C. Test Complete Flow
1. Connect new device to WiFi
2. Select a plan
3. Enter phone number and pay
4. Verify internet access is granted

### 7. **Troubleshooting**

#### Common Issues:

**Issue**: "Connection refused" when redirecting
- **Solution**: Check Django server is running and accessible from MikroTik IP

**Issue**: RADIUS authentication fails
- **Solution**: Verify RADIUS secret matches in both MikroTik and FreeRADIUS

**Issue**: Payment fails
- **Solution**: Check KCB Buni API configuration and network connectivity

**Issue**: Users don't get redirected
- **Solution**: Verify walled garden configuration allows access to Django server

### 8. **Security Considerations**

1. **Use HTTPS in production**
2. **Restrict Django ALLOWED_HOSTS**
3. **Secure RADIUS secrets**
4. **Configure proper firewall rules**
5. **Regular security updates**

### 9. **Monitoring and Logs**

#### Django Logs
Monitor Django logs for payment and authentication issues:
```bash
tail -f wifi_billing.log
```

#### MikroTik Logs
Monitor MikroTik system logs:
```
/log print where topics~"hotspot"
```

#### RADIUS Logs
Monitor FreeRADIUS logs for authentication:
```bash
tail -f /var/log/freeradius/radius.log
```

## Next Steps

1. Configure SSL certificates for HTTPS
2. Set up monitoring and alerting
3. Implement backup and recovery procedures
4. Scale for multiple locations
5. Add advanced features (bandwidth monitoring, user management, etc.)