# ✅ Railway Deployment Checklist

## Pre-Deployment
- [ ] All code committed to Git repository
- [ ] `.env` file removed from repository (sensitive data)
- [ ] `requirements.txt` updated with all dependencies
- [ ] Database migrations created and ready
- [ ] Static files directory exists
- [ ] All apps added to `INSTALLED_APPS`

## Railway Setup
- [ ] Railway account created
- [ ] Repository connected to Railway
- [ ] PostgreSQL database added to project
- [ ] Environment variables configured

## Required Environment Variables
- [ ] `SECRET_KEY` - New Django secret key generated
- [ ] `DEBUG` - Set to `False`
- [ ] `ALLOWED_HOSTS` - Your Railway domain added
- [ ] `DATABASE_URL` - Automatically set by Railway PostgreSQL
- [ ] `SITE_URL` - Your Railway app URL

## Optional Environment Variables
- [ ] `MIKROTIK_API_HOST` - Default router IP
- [ ] `MIKROTIK_API_USERNAME` - Default router username  
- [ ] `MIKROTIK_API_PASSWORD` - Default router password
- [ ] `KCB_BUNI_CLIENT_ID` - Payment gateway credentials
- [ ] `KCB_BUNI_CLIENT_SECRET` - Payment gateway credentials
- [ ] `KCB_BUNI_API_KEY` - Payment gateway credentials
- [ ] `EMAIL_HOST` - SMTP server for emails
- [ ] `EMAIL_HOST_USER` - Email username
- [ ] `EMAIL_HOST_PASSWORD` - Email password
- [ ] `DJANGO_SUPERUSER_USERNAME` - Admin username
- [ ] `DJANGO_SUPERUSER_PASSWORD` - Admin password
- [ ] `SENTRY_DSN` - Error monitoring

## Post-Deployment Testing
- [ ] Application loads successfully
- [ ] Database migrations applied
- [ ] Static files loading (CSS/JS)
- [ ] Admin panel accessible (`/admin/`)
- [ ] Admin user can login
- [ ] WiFi plans page loads (`/plans/`)
- [ ] API endpoints working (`/api/plans/`)
- [ ] MikroTik station can be added
- [ ] Station config files can be downloaded
- [ ] Login page contains correct URLs

## Production Readiness
- [ ] Custom domain configured (optional)
- [ ] SSL certificate working
- [ ] All sensitive data in environment variables
- [ ] Error monitoring configured
- [ ] Database backups enabled
- [ ] Logs monitoring setup

## MikroTik Integration
- [ ] At least one station configured in dashboard
- [ ] MikroTik router configured with:
  - [ ] Hotspot service enabled
  - [ ] RADIUS server pointing to your Django app
  - [ ] Custom login page uploaded
  - [ ] Walled garden configured for your domain
- [ ] Test user flow: Connect → Login → Select Plan → Payment

## Payment Integration (Optional)
- [ ] KCB Buni credentials configured
- [ ] Payment flow tested
- [ ] Success/failure pages working
- [ ] Payment status updates correctly

## Final Verification
- [ ] End-to-end user flow tested
- [ ] Performance acceptable under load
- [ ] All error pages display correctly
- [ ] Mobile responsiveness verified
- [ ] Browser compatibility tested

---

🎉 **Ready to go live!** Your WiFi Billing System is production-ready on Railway.