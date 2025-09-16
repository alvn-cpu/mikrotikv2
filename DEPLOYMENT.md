# 🚀 WiFi Billing System - Railway Deployment Guide

This guide will walk you through deploying your Django WiFi Billing System to Railway.com.

## 📋 Prerequisites

- [Railway.com account](https://railway.app/) (free tier available)
- Git repository with your code
- Basic knowledge of environment variables

## 🛠️ Deployment Steps

### Step 1: Prepare Your Repository

Ensure you have all the deployment files (these are already created):
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway startup commands  
- ✅ `railway.json` - Railway configuration
- ✅ `.env.example` - Environment variables template
- ✅ Updated `settings.py` - Production configuration

### Step 2: Deploy to Railway

#### Option A: Deploy from GitHub (Recommended)

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Connect to Railway**:
   - Go to [railway.app](https://railway.app/)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your WiFi Billing System repository

#### Option B: Deploy using Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

### Step 3: Add PostgreSQL Database

1. In your Railway dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically create a PostgreSQL instance
4. The `DATABASE_URL` will be automatically added to your environment variables

### Step 4: Configure Environment Variables

In your Railway project dashboard, go to **"Variables"** tab and add:

#### Required Variables:
```bash
# Django Configuration
SECRET_KEY=your-super-secret-key-here-generate-a-new-one
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app,yourdomain.com
SITE_URL=https://your-app-name.railway.app

# Database (automatically provided by Railway PostgreSQL)
DATABASE_URL=postgresql://... (automatically set)

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# MikroTik Default Configuration
MIKROTIK_API_HOST=192.168.1.1
MIKROTIK_API_USERNAME=admin
MIKROTIK_API_PASSWORD=your-mikrotik-password
```

#### Optional Variables:
```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# KCB Buni Payment Gateway
KCB_BUNI_CLIENT_ID=your-client-id
KCB_BUNI_CLIENT_SECRET=your-client-secret
KCB_BUNI_API_KEY=your-api-key

# Admin User (for automatic creation)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=secure-admin-password

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn-here
```

### Step 5: Generate Secret Key

Generate a new Django secret key:
```python
# Run this in Python:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 6: Deploy and Initialize

1. **Trigger deployment**: Railway will automatically deploy when you push to GitHub
2. **Monitor deployment**: Check the "Deployments" tab for progress
3. **Check logs**: Use Railway's built-in logging to monitor the deployment

### Step 7: Post-Deployment Setup

Once deployed successfully:

1. **Access your admin panel**: `https://your-app.railway.app/admin/`
2. **Login with superuser** (if you set the environment variables)
3. **Configure your first MikroTik station**:
   - Go to Dashboard → Stations → Add Station
   - Add your router details and payment settings

## 🔧 Custom Domain Setup (Optional)

1. In Railway dashboard, go to **"Settings"** → **"Domains"**
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `yourdomain.com`)
4. Update your DNS records as instructed
5. Update `ALLOWED_HOSTS` and `SITE_URL` environment variables

## 📊 Monitoring and Logs

### View Application Logs
```bash
# Using Railway CLI
railway logs

# Or check the Railway dashboard "Logs" tab
```

### Health Check Endpoints
- Application: `https://your-app.railway.app/admin/`
- API: `https://your-app.railway.app/api/plans/`
- Plans: `https://your-app.railway.app/plans/`

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
**Problem**: `django.db.utils.OperationalError: could not connect to server`
**Solution**: Ensure PostgreSQL service is running and `DATABASE_URL` is set

#### 2. Static Files Not Loading
**Problem**: CSS/JS files not loading (404 errors)
**Solution**: 
- Ensure `whitenoise` is in `requirements.txt`
- Check `STATIC_URL` and `STATICFILES_STORAGE` settings
- Run `python manage.py collectstatic` manually if needed

#### 3. Environment Variables Not Working
**Problem**: Settings not applying from environment variables
**Solution**:
- Double-check variable names in Railway dashboard
- Restart the deployment after adding variables
- Check for typos in variable names

#### 4. Import Errors
**Problem**: `ModuleNotFoundError` for specific packages
**Solution**:
- Ensure all dependencies are in `requirements.txt`
- Check for version conflicts
- Deploy again to reinstall packages

### Debug Commands

```bash
# Check if deployment is successful
railway status

# View environment variables
railway variables

# Check service logs
railway logs --tail

# Connect to database (if needed)
railway connect postgresql
```

## 🔄 Updates and Maintenance

### Updating Your Application

1. **Make changes locally**
2. **Test thoroughly**
3. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```
4. **Railway automatically deploys** the changes

### Database Backup

Railway provides automatic backups for PostgreSQL, but you can also create manual backups:

```bash
# Using Railway CLI
railway connect postgresql
# Then use pg_dump commands as needed
```

## 🎯 Production Checklist

Before going live:

- [ ] **Security**: All sensitive data in environment variables
- [ ] **Domain**: Custom domain configured and SSL working
- [ ] **Database**: PostgreSQL connected and migrations applied
- [ ] **Static Files**: All CSS/JS loading correctly
- [ ] **Admin Access**: Admin user created and accessible
- [ ] **Plans**: WiFi plans configured and visible
- [ ] **MikroTik**: At least one router/station configured
- [ ] **Payments**: KCB Buni credentials configured (if using payments)
- [ ] **Testing**: Full user flow tested (plan selection → payment → access)
- [ ] **Monitoring**: Error tracking configured (Sentry recommended)
- [ ] **Backup**: Database backup strategy in place

## 🆘 Support

If you encounter issues:

1. **Check Railway logs** first
2. **Review environment variables**
3. **Test locally** with same environment variables
4. **Check Railway's status page** for service issues
5. **Review Django deployment best practices**

## 🌟 Additional Features

After successful deployment, consider:

- **Redis integration** for caching and Celery
- **CDN setup** for static files
- **Monitoring dashboard** (e.g., Grafana)
- **Automated testing** with GitHub Actions
- **Staging environment** for testing

---

**🎉 Congratulations!** Your WiFi Billing System is now live on Railway!

Remember to update your MikroTik login page URLs to point to your new production domain.