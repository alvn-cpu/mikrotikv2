# Dynamic URL Detection Setup Guide

## Overview

The station configuration system now **automatically detects** whether you're running locally or in production and generates the correct URLs for the custom login pages.

## How It Works

### 🏠 **Local Development** (what you're doing now)
- **Detected when**: `DEBUG=True` or running on `127.0.0.1`/`localhost`
- **Generated URLs**: `http://127.0.0.1:8000/plans/...`
- **Login page redirects to**: Your local Django server

### 🌐 **Production Deployment** (when you host your app)
- **Detected when**: Custom domain in `ALLOWED_HOSTS` or `SITE_URL` configured
- **Generated URLs**: `https://yourdomain.com/plans/...`
- **Login page redirects to**: Your production server

## Configuration Options

### Option 1: Automatic Detection (Recommended)
No configuration needed! The system automatically detects:

```python
# Local development - automatically detects
# Generated URL: http://127.0.0.1:8000

# Production - automatically detects from ALLOWED_HOSTS
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
# Generated URL: https://yourdomain.com
```

### Option 2: Manual Configuration (Advanced)
Add this to your `wifi_billing/settings.py` for explicit control:

```python
# For local development
SITE_URL = 'http://127.0.0.1:8000'

# For production (when you deploy)
SITE_URL = 'https://yourdomain.com'

# Or for custom port/IP
SITE_URL = 'http://192.168.1.100:8080'
```

## Testing Right Now (Local Development)

### 1. Create a Test Station
```bash
# In your project directory
python manage.py shell
```

```python
from mikrotik_integration.models import RouterConfig

station = RouterConfig.objects.create(
    name='Test_Local_Station',
    host='192.168.1.1',
    username='admin',
    password='test123',
    business_name='My Local WiFi Test'
)

print(f"Created station with ID: {station.id}")
exit()
```

### 2. Download the Login Page
1. Go to **Dashboard** → **Stations**
2. Find your test station
3. Click **Download** dropdown → **Login Page (.html)**
4. Open the downloaded file and search for "billingServerUrl"
5. You should see: `var billingServerUrl = "http://127.0.0.1:8000";`

## When You Deploy to Production

### 1. Update Your Settings
```python
# In wifi_billing/settings.py
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    # Remove localhost/127.0.0.1 in production
]

DEBUG = False  # Important for production

# Optional: Explicit URL
SITE_URL = 'https://yourdomain.com'
```

### 2. Generate New Configurations
After deploying, generate new station configurations:
1. The system will automatically detect production environment
2. Generated login pages will use: `https://yourdomain.com/plans/...`
3. MikroTik walled garden will include your production domain

## File Examples

### Local Development Login Page
```html
<script>
function redirectToBilling() {
    var billingServerUrl = "http://127.0.0.1:8000";
    var redirectUrl = billingServerUrl + "/plans/" + 
                     "?mac=" + encodeURIComponent(deviceMac) + 
                     "&ip=" + encodeURIComponent(deviceIp) + 
                     "&station_id=1";
    window.location.href = redirectUrl;
}
</script>
```

### Production Login Page (Auto-generated when deployed)
```html
<script>
function redirectToBilling() {
    var billingServerUrl = "https://yourdomain.com";
    var redirectUrl = billingServerUrl + "/plans/" + 
                     "?mac=" + encodeURIComponent(deviceMac) + 
                     "&ip=" + encodeURIComponent(deviceIp) + 
                     "&station_id=1";
    window.location.href = redirectUrl;
}
</script>
```

## Detection Logic

The system checks in this order:

1. **`SITE_URL` setting** (if configured)
2. **Production domains** in `ALLOWED_HOSTS` (domains with dots, not localhost/IPs)
3. **DEBUG=False** with valid hosts
4. **Default to local**: `http://127.0.0.1:8000`

## Quick Test Commands

### Test Auto-Detection
```python
# In Django shell
from dashboard.station_config_generator import get_server_url

print("Detected URL:", get_server_url())
# Should show: http://127.0.0.1:8000 (for local development)
```

### Test Login Page Generation
```python
from mikrotik_integration.models import RouterConfig
from dashboard.station_config_generator import generate_station_login_page

station = RouterConfig.objects.first()
if station:
    login_page = generate_station_login_page(station)
    # Check if login_page contains the correct URL
    if "127.0.0.1:8000" in login_page:
        print("✅ Local development URL detected correctly!")
    else:
        print("❌ URL detection may need adjustment")
```

## Benefits

✅ **Seamless Development**: Works immediately on localhost  
✅ **Easy Deployment**: Automatically switches to production URLs  
✅ **No Manual Updates**: Station configs update automatically  
✅ **Flexible Configuration**: Support for custom domains/ports  
✅ **Security Aware**: Uses HTTPS for production domains  

## Troubleshooting

### Issue: Login page shows wrong URL
**Solution**: Check your `ALLOWED_HOSTS` and `DEBUG` settings

### Issue: Still shows "YOUR_DJANGO_SERVER_IP"
**Solution**: The old template is cached, generate a new configuration

### Issue: HTTPS not working
**Solution**: Ensure your production domain is properly configured with SSL

---

Your station login pages will now **automatically work** for both local testing and production deployment! 🎉