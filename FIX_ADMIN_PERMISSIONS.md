# 🔧 Fix Admin Permissions Issue

## Problem
You see the error: "You are authenticated as admin, but are not authorized to access this page."

This means the user `admin` exists but doesn't have the proper Django admin permissions.

## 🚀 Quick Fix Options

### Option 1: Web Interface (Easiest)
Visit this URL in your browser:
```
https://beat-production-5003.up.railway.app/fix-admin-permissions/?token=broadcom2024
```

This will automatically fix the admin user permissions and show you the status.

### Option 2: Using Railway CLI
If you have Railway CLI installed:
```bash
# Connect to your Railway project
railway shell

# Run the fix command
python manage.py fix_admin_permissions --username admin
```

### Option 3: Through Django Admin Shell (if you can access it)
```python
# Connect to Railway shell
railway shell

# Open Django shell
python manage.py shell

# Run these commands:
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()
print("✅ Admin permissions fixed!")
```

## 🔍 What This Does

The fix will:
- ✅ Set `is_staff = True` (required for admin access)
- ✅ Set `is_superuser = True` (full admin privileges)  
- ✅ Set `is_active = True` (account is enabled)
- ✅ Optionally reset the password

## 🧪 Testing

After running the fix:

1. **Visit the Django admin**: https://beat-production-5003.up.railway.app/admin/
2. **Login with**: 
   - Username: `admin`
   - Password: `admin` (or whatever you set)
3. **You should now have full access** to the admin panel

## 🔗 Access URLs

- **Fix Permissions**: https://beat-production-5003.up.railway.app/fix-admin-permissions/?token=broadcom2024
- **Django Admin**: https://beat-production-5003.up.railway.app/admin/
- **Custom Login**: https://beat-production-5003.up.railway.app/auth/login/
- **Dashboard**: https://beat-production-5003.up.railway.app/dashboard/

## ⚠️ Security Note

The web fix endpoint uses a simple token (`broadcom2024`) for security. In production, you should:
1. Change the token by setting `ADMIN_FIX_TOKEN` environment variable
2. Remove the endpoint after fixing the issue
3. Use strong passwords for admin users

## 🆘 Still Having Issues?

If the fix doesn't work:
1. Check the Railway logs for error messages
2. Try creating a new superuser with a different username
3. Contact support with the error details

## 📋 Next Steps

After fixing admin access:
1. **Set up Google OAuth** (see `GOOGLE_OAUTH_SETUP.md`)
2. **Configure KCB Buni payments** (see `KCB_SETUP_CHECKLIST.md`)
3. **Add your WiFi stations** in the admin panel
4. **Test the complete system** with your users