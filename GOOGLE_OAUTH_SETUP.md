# 🔑 Google OAuth Setup Guide

## Overview
This guide will help you set up Google OAuth authentication for your BROADCOM NETWORKS WiFi billing system.

## 📋 Prerequisites
- Google account
- Access to Google Cloud Console
- Railway deployment URL: `https://beat-production-5003.up.railway.app`

## 🚀 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. **Visit Google Cloud Console**: https://console.cloud.google.com
2. **Create a New Project**:
   - Click "Select a Project" → "New Project"
   - Project Name: `BROADCOM NETWORKS WiFi`
   - Click "Create"

### Step 2: Enable Google+ API

1. **Navigate to APIs & Services** → **Library**
2. **Search for "Google+ API"** and enable it
3. **Also enable "Google Identity"** (if available)

### Step 3: Configure OAuth Consent Screen

1. **Go to APIs & Services** → **OAuth consent screen**
2. **Choose "External"** (unless you have Google Workspace)
3. **Fill in required information**:
   - App name: `BROADCOM NETWORKS`
   - User support email: Your email
   - App domain: `beat-production-5003.up.railway.app`
   - Developer contact email: Your email
4. **Add scopes**:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. **Save and Continue**

### Step 4: Create OAuth Credentials

1. **Go to APIs & Services** → **Credentials**
2. **Click "Create Credentials"** → **OAuth 2.0 Client IDs**
3. **Configure the OAuth client**:
   - Application type: `Web application`
   - Name: `BROADCOM NETWORKS Web Client`
   
4. **Add Authorized URLs**:
   
   **Authorized JavaScript origins**:
   ```
   https://beat-production-5003.up.railway.app
   ```
   
   **Authorized redirect URIs**:
   ```
   https://beat-production-5003.up.railway.app/accounts/google/login/callback/
   ```

5. **Click "Create"**
6. **Copy the credentials**:
   - Client ID (starts with numbers, ends with `.apps.googleusercontent.com`)
   - Client Secret

### Step 5: Configure Railway Environment Variables

Add these environment variables in your Railway project:

```bash
# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

### Step 6: Update Django Settings

Your settings are already configured, but verify these are present:

```python
# In wifi_billing_system/settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}
```

### Step 7: Add Google Social Application in Django Admin

After deployment, you need to configure the Google app in Django admin:

1. **Visit your admin panel**: https://beat-production-5003.up.railway.app/admin/
2. **Go to Sites** → **Social Applications**
3. **Add a new Social Application**:
   - Provider: `Google`
   - Name: `Google OAuth`
   - Client ID: Your Google Client ID
   - Secret Key: Your Google Client Secret
   - Sites: Select your site (`BROADCOM NETWORKS`)

## 🛠️ Alternative: Database Setup via Management Command

I'll create a management command to set this up automatically.

## 🧪 Testing the Integration

1. **Visit**: https://beat-production-5003.up.railway.app/auth/login/
2. **Click "Continue with Google"**
3. **You should be redirected to Google's OAuth consent screen**
4. **After authorization, you should be redirected back to your dashboard**

## 🚨 Troubleshooting

### Common Issues:

1. **"redirect_uri_mismatch" error**:
   - Check that your redirect URI exactly matches what's in Google Console
   - Must be: `https://beat-production-5003.up.railway.app/accounts/google/login/callback/`

2. **"invalid_client" error**:
   - Verify Client ID and Secret are correct
   - Make sure they're properly set in Railway environment variables

3. **500 Server Error**:
   - Check Django logs for specific error
   - Usually means Social Application is not configured in admin

4. **"Access blocked" error**:
   - Your app is still in testing mode
   - Either publish your app or add test users in Google Console

## 🔐 Security Considerations

- Keep your Client Secret secure
- Never commit OAuth credentials to version control
- Use environment variables only
- Regularly rotate your credentials
- Monitor OAuth usage in Google Console

## 📱 Testing URLs

- **Login Page**: https://beat-production-5003.up.railway.app/auth/login/
- **Google OAuth**: https://beat-production-5003.up.railway.app/accounts/google/login/
- **Admin Panel**: https://beat-production-5003.up.railway.app/admin/
- **Dashboard**: https://beat-production-5003.up.railway.app/dashboard/

## ✅ Verification Checklist

- [ ] Google Cloud project created
- [ ] OAuth consent screen configured
- [ ] OAuth 2.0 client created with correct redirect URIs
- [ ] Environment variables set in Railway
- [ ] Social Application configured in Django admin
- [ ] Site configuration updated
- [ ] Testing successful login flow