# Station Configuration Download Feature - User Guide

## Overview

The WiFi Billing System now provides comprehensive station configuration downloads for easy MikroTik router deployment. When you create a new station, you can download customized configuration files specific to that station.

## What You Get

After creating a station, you can download:

### 1. **Complete Configuration Package (ZIP)** ⭐ *Recommended*
- **File**: `{StationName}_complete_config.zip`
- **Contains**:
  - RouterOS configuration script (`.rsc`)
  - Custom login page (`.html`)
  - Setup instructions (`.txt`)

### 2. **RouterOS Configuration Only**
- **File**: `{StationName}_config.rsc`
- **Contains**: MikroTik RouterOS commands for complete router setup

### 3. **Custom Login Page Only**
- **File**: `{StationName}_login.html`
- **Contains**: Branded captive portal page for the station

## How to Use

### Step 1: Create a Station
1. Go to **Dashboard** → **Stations**
2. Click **"Add New Station"**
3. Fill in the required information:
   - **Station Name**: Unique identifier
   - **IP Address**: Router's IP address
   - **API Credentials**: Username/password for router access
   - **Business Name**: Will appear on login page
   - **Payment Configuration**: KCB account details

4. Click **"Save Station"**

### Step 2: Download Configuration
1. In the stations table, find your newly created station
2. Click the **Download** dropdown button (green button with download icon)
3. Choose your preferred download option:

   - **📦 Complete Package (ZIP)**: Everything you need in one file
   - **📄 RouterOS Config (.rsc)**: Just the router configuration
   - **🌐 Login Page (.html)**: Just the custom login page

### Step 3: Deploy to MikroTik Router

#### For Complete Package:
1. Extract the ZIP file
2. Read the `{StationName}_README.txt` file for detailed instructions
3. Upload `{StationName}_config.rsc` to your MikroTik router
4. Import the configuration: `/import {StationName}_config.rsc`
5. Upload `{StationName}_login.html` to the hotspot folder as `login.html`
6. Configure WAN connection (ether1)
7. Update RADIUS server IP to your Django server IP

## What Makes Each Station Unique

Each downloaded configuration is customized with:

- **Unique Network Range**: Avoids IP conflicts between stations
- **Station-Specific RADIUS Secret**: Enhanced security
- **Custom Branding**: Business name and station information
- **Payment Integration**: Station's specific KCB account details
- **Proper Walled Garden**: Access to billing system and payment APIs

## Configuration Features

### Automatic Network Assignment
- **Main Router (ID 1)**: `192.168.100.0/24`
- **Second Router (ID 2)**: `192.168.101.0/24`
- **And so on...**: Each station gets a unique subnet

### Security Features
- Unique RADIUS secrets per station
- Proper firewall rules
- Secure API access configuration
- Payment gateway access in walled garden

### Hotspot Features
- Pre-configured user profiles for different plans
- Automatic RADIUS authentication
- Custom login page with station branding
- Proper DHCP and DNS configuration

## Troubleshooting

### Common Issues:

1. **"Config import failed"**
   - Solution: Check MikroTik RouterOS version compatibility
   - Ensure you're using the correct import command

2. **"Users not redirected to billing system"**
   - Solution: Update `YOUR_DJANGO_SERVER_IP` in the configuration
   - Add your server IP to walled garden

3. **"RADIUS authentication fails"**
   - Solution: Add the station's RADIUS secret to your billing system
   - Check that RADIUS server is running

4. **"Custom login page not showing"**
   - Solution: Ensure login.html is in the correct hotspot folder
   - Verify hotspot profile is using the correct HTML directory

### Pre-deployment Checklist:

✅ Station created and saved in billing system  
✅ Configuration downloaded and extracted  
✅ Django server IP updated in configuration  
✅ RADIUS secret added to billing system  
✅ MikroTik router accessible and ready  
✅ Internet connection configured on ether1  
✅ Custom login page uploaded to hotspot folder  

## Advanced Configuration

### Custom Business Branding
- Edit the business name in station settings
- Login page will automatically use your branding
- Add custom colors by modifying the CSS in login page

### Payment Integration
- Configure KCB account type (Paybill, Till, or Bank Account)
- Add account numbers and holder names
- Test payment credentials in dashboard

### Network Customization
- Each station gets a unique IP range automatically
- Modify DHCP ranges in the configuration if needed
- Ensure no conflicts with existing networks

## Support

- **Documentation**: Check README.txt in downloaded package
- **Station Management**: Use dashboard for ongoing management  
- **Payment Issues**: Test credentials using dashboard tools
- **MikroTik Help**: Refer to RouterOS documentation

## Benefits

✅ **Quick Deployment**: Complete configuration in minutes  
✅ **No Conflicts**: Each station has unique network settings  
✅ **Professional Look**: Custom branded login pages  
✅ **Secure**: Unique RADIUS secrets and firewall rules  
✅ **Payment Ready**: Pre-configured for KCB Buni integration  
✅ **Easy Updates**: Re-download if you change station settings  

---

**Note**: Always backup your existing MikroTik configuration before importing new settings. The generated configuration is designed for clean RouterOS installations.