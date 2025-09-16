# KCB Buni Payment Integration Setup Guide

## Overview

The WiFi Billing System now uses a hybrid approach for KCB Buni integration:
- **Global API credentials** are configured once in the system settings
- **Station-specific account details** are configured per station

This allows multiple stations to share the same KCB developer account while each having their own payment destination (paybill, till number, or bank account).

## Configuration Steps

### 1. Global API Credentials Setup

Set the following environment variables in your `.env` file:

```bash
# KCB Buni API Configuration
KCB_BUNI_BASE_URL=https://api.kcbbuni.com
KCB_BUNI_CLIENT_ID=your-kcb-client-id
KCB_BUNI_CLIENT_SECRET=your-kcb-client-secret  
KCB_BUNI_API_KEY=your-kcb-api-key
```

**How to get these credentials:**
1. Visit the KCB Buni Developer Portal
2. Create a developer account or log in
3. Create a new application
4. Copy the Client ID, Client Secret, and API Key
5. These credentials will be used by all stations

### 2. Station-Specific Configuration

For each station, configure the following in the admin dashboard:

#### Station Payment Configuration
- **Business Name**: Name displayed to customers
- **Payment Method**: Choose from Paybill, Till, or Bank Account  
- **Enable Payments**: Toggle to activate payments for this station

#### KCB Account Details
- **Account Type**: Select the type of account (Paybill, Till, or Bank)
- **Account/Till/Paybill Number**: The actual number customers will pay to
- **Account Name/Reference**: Optional reference for paybill transactions

### 3. Account Type Examples

#### Paybill Configuration
- **Account Type**: Paybill
- **Account Number**: 123456 (your paybill number)
- **Account Name**: Station WiFi (optional reference)

#### Till Number Configuration  
- **Account Type**: Till
- **Account Number**: 234567 (your till number)
- **Account Name**: (not used for till payments)

#### Bank Account Configuration
- **Account Type**: Bank
- **Account Number**: 1234567890 (your bank account number)
- **Account Name**: Station Owner Name

## Database Migration

The RouterConfig model has been updated with new fields:

```python
# New fields added:
kcb_account_type = models.CharField(max_length=20, choices=KCB_ACCOUNT_TYPES, default='paybill')
kcb_account_number = models.CharField(max_length=50, blank=True)
account_name = models.CharField(max_length=100, blank=True)
```

Run the migration to update your database:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Benefits of This Setup

1. **Centralized API Management**: One set of API credentials for all stations
2. **Flexible Payment Destinations**: Each station can have different payment accounts
3. **Easier Maintenance**: API credentials are managed globally, not per station
4. **Better Security**: API credentials are stored in environment variables
5. **Scalability**: Easy to add new stations without API credential duplication

## Testing the Integration

1. **Test API Connectivity**: Use the "Test Payment Configuration" button in the station management interface
2. **Validate Credentials**: The system will check both global API credentials and station account details
3. **Monitor Logs**: Check the application logs for any integration issues

## Troubleshooting

### Common Issues

1. **"Global API credentials missing"**: Check your `.env` file and restart the application
2. **"Invalid account type"**: Ensure account type is one of: paybill, till, bank
3. **"Failed to authenticate with KCB Buni API"**: Verify your API credentials with KCB Buni
4. **"Account number missing"**: Each station must have an account number configured

### Log Files

Check the application logs at `wifi_billing.log` for detailed error messages.

### Support

For KCB Buni API issues, contact KCB Buni developer support with your Client ID.

## Migration from Old Setup

If you were previously using station-specific API credentials:

1. **Backup your database** before making changes
2. **Set up global credentials** in your `.env` file
3. **Update each station** with their specific account details
4. **Remove old credential fields** from station configurations
5. **Test the integration** thoroughly before going live

## Security Considerations

- Never commit API credentials to version control
- Use environment variables for all sensitive configuration
- Regularly rotate API credentials as recommended by KCB Buni  
- Monitor API usage and payment transactions for anomalies
- Use HTTPS in production to protect API communication