# 📋 KCB Buni Setup Checklist

## ✅ Pre-Requirements Checklist

### Business Documents Needed:
- [ ] Business registration certificate
- [ ] KCB business bank account 
- [ ] Tax PIN certificate
- [ ] Business permit/license
- [ ] ID copies of directors/owners
- [ ] Business profile/company profile

### Technical Requirements:
- [ ] Domain name for your system (for callbacks)
- [ ] SSL certificate (HTTPS required)
- [ ] Static IP or reliable hosting (Railway/Heroku)
- [ ] Webhook endpoints properly configured

## 🏦 KCB Bank Application Process

### Step 1: Visit KCB Branch
- [ ] Go to your nearest KCB branch
- [ ] Request "KCB Buni API Integration Application"
- [ ] Submit all required business documents
- [ ] Get application reference number

### Step 2: KCB Buni Developer Portal Access
- [ ] Wait for KCB approval (3-5 business days)
- [ ] Receive developer portal access credentials
- [ ] Login to KCB Buni developer portal
- [ ] Create new application/project

### Step 3: API Credentials Generation
- [ ] Generate sandbox API credentials for testing:
  - [ ] Sandbox Client ID
  - [ ] Sandbox Client Secret  
  - [ ] Sandbox API Key
- [ ] Generate production API credentials:
  - [ ] Production Client ID
  - [ ] Production Client Secret
  - [ ] Production API Key

## 🔧 System Configuration

### Step 4: Configure Environment Variables
Add to your `.env` file:
```bash
# KCB Buni API Configuration
KCB_BUNI_BASE_URL=https://sandbox.kcbbuni.com  # Use sandbox first
KCB_BUNI_CLIENT_ID=your-sandbox-client-id
KCB_BUNI_CLIENT_SECRET=your-sandbox-client-secret
KCB_BUNI_API_KEY=your-sandbox-api-key
```

### Step 5: Configure Station Payment Details
For each WiFi station in Django Admin:
- [ ] Set Business Name
- [ ] Choose Account Type (Paybill/Till/Bank)
- [ ] Enter Account Number
- [ ] Set Account Name/Reference
- [ ] Enable Payments
- [ ] Test Configuration

## 🧪 Testing Phase

### Step 6: Sandbox Testing
- [ ] Test API authentication
- [ ] Test STK Push initiation
- [ ] Test payment callbacks
- [ ] Test payment status checking
- [ ] Test transaction reversal (if needed)

### Step 7: Production Migration
After successful testing:
- [ ] Update environment variables to production URLs
- [ ] Update API credentials to production
- [ ] Update KCB with production callback URLs
- [ ] Test with small amounts first
- [ ] Monitor logs for issues

## 📞 KCB Contact Information

### For API Issues:
- **KCB Digital Banking**: (Call KCB customer care)
- **Developer Support**: Available through developer portal
- **Business Banking**: Your relationship manager

### For Business Account Issues:
- **KCB Customer Care**: 0711 087 000
- **Email**: customercare@kcbgroup.com
- **Visit**: Any KCB branch

## 🔒 Security Considerations

### API Security:
- [ ] Never commit API credentials to code
- [ ] Use environment variables only
- [ ] Implement proper webhook validation
- [ ] Use HTTPS for all API communications
- [ ] Monitor API usage and transactions
- [ ] Set up transaction alerts
- [ ] Implement rate limiting

### Business Security:
- [ ] Regular reconciliation of payments
- [ ] Monitor for suspicious transactions
- [ ] Set up daily/monthly reports
- [ ] Implement refund procedures
- [ ] Document payment processes

## 🚀 Go-Live Checklist

### Final Checks:
- [ ] All tests passing in sandbox
- [ ] Production credentials configured
- [ ] Callback URLs updated with KCB
- [ ] Monitoring and alerts set up
- [ ] Staff trained on payment system
- [ ] Customer support procedures ready
- [ ] Refund/reversal procedures documented

## 📊 Monitoring & Maintenance

### Ongoing Tasks:
- [ ] Daily transaction monitoring
- [ ] Weekly reconciliation with KCB
- [ ] Monthly API usage review
- [ ] Regular backup of transaction data
- [ ] Update API credentials as needed
- [ ] Monitor system performance

## 🆘 Troubleshooting Common Issues

### Authentication Failures:
1. Check API credentials are correct
2. Verify account is active with KCB
3. Check API rate limits
4. Verify callback URLs are accessible

### Payment Failures:
1. Check customer has sufficient funds
2. Verify phone number format (254XXXXXXXXX)
3. Check if till/paybill is active
4. Review KCB API documentation

### Callback Issues:
1. Verify callback URLs are HTTPS
2. Check webhook endpoint is accessible
3. Validate callback signature
4. Review callback processing logs

## 📝 Next Steps After Setup

1. **Train Your Team**
   - How to monitor payments
   - How to handle customer complaints
   - How to process refunds

2. **Set Up Monitoring**
   - Payment success rates
   - Failed transaction alerts
   - Daily reconciliation reports

3. **Customer Communications**
   - Payment instructions for customers
   - Troubleshooting guide for staff
   - Customer support procedures

## 🎉 Success Metrics

Your KCB integration is successful when:
- [ ] >95% payment success rate
- [ ] <30 second payment processing time
- [ ] Automatic payment confirmations working
- [ ] Customer complaints minimal
- [ ] Daily reconciliation matches KCB reports