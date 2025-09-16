"""
KCB Buni API Integration Service
Handles STK Push, payment status checking, and transaction management
"""

import requests
import json
import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class KCBBuniService:
    """
    KCB Buni API Service Class
    Handles all KCB Buni API interactions for M-Pesa payments
    """
    
    def __init__(self, station_config=None):
        """
        Initialize KCB Buni service with global API credentials and station-specific account details
        
        Args:
            station_config: RouterConfig instance with station account details
        """
        self.base_url = getattr(settings, 'KCB_BUNI_BASE_URL', 'https://api.kcbbuni.com')
        
        # Always use global API credentials
        self.client_id = getattr(settings, 'KCB_BUNI_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'KCB_BUNI_CLIENT_SECRET', '')
        self.api_key = getattr(settings, 'KCB_BUNI_API_KEY', '')
        
        if station_config:
            # Use station-specific account details
            self.account_type = station_config.kcb_account_type
            self.account_number = station_config.kcb_account_number
            self.account_name = station_config.account_name or station_config.business_name
            self.business_name = station_config.business_name or f'Station {station_config.name}'
        else:
            # Use default values
            self.account_type = 'paybill'
            self.account_number = ''
            self.account_name = ''
            self.business_name = 'WiFi Billing System'
    
    def get_access_token(self):
        """
        Get OAuth access token from KCB Buni API
        Uses caching to avoid frequent token requests
        """
        cache_key = f'kcb_token_{self.client_id}'
        token = cache.get(cache_key)
        
        if token:
            return token
        
        try:
            # Prepare authentication
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-Key': self.api_key
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'read write'
            }
            
            response = requests.post(
                f'{self.base_url}/oauth/token',
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # Cache token for 90% of its lifetime
                cache.set(cache_key, access_token, expires_in * 0.9)
                
                logger.info("KCB Buni access token obtained successfully")
                return access_token
            else:
                logger.error(f"Failed to get KCB access token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting KCB access token: {str(e)}")
            return None
    
    def initiate_stk_push(self, phone_number, amount, plan_name, reference=None):
        """
        Initiate STK Push payment request
        
        Args:
            phone_number (str): Customer phone number (254XXXXXXXXX format)
            amount (float): Amount to charge
            plan_name (str): Name of the plan being purchased
            reference (str): Optional reference number
            
        Returns:
            dict: API response with transaction details
        """
        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # Generate unique transaction reference
            if not reference:
                reference = f"WIFI_{int(time.time())}_{phone_number[-4:]}"
            
            # Prepare payment data based on account type
            if self.account_type == 'paybill':
                payload = {
                    'phoneNumber': phone_number,
                    'amount': str(int(amount)),
                    'accountReference': self.account_name or reference,
                    'transactionDesc': f'{self.business_name} - {plan_name}',
                    'merchantRequestID': reference,
                    'checkoutRequestID': f"ws_CO_{int(time.time())}",
                    'businessShortCode': self.account_number,
                    'callBackURL': f"{settings.SITE_URL}/payments/kcb/callback/",
                    'queueTimeOutURL': f"{settings.SITE_URL}/payments/kcb/timeout/"
                }
            elif self.account_type == 'till':
                payload = {
                    'phoneNumber': phone_number,
                    'amount': str(int(amount)),
                    'transactionDesc': f'{self.business_name} - {plan_name}',
                    'merchantRequestID': reference,
                    'checkoutRequestID': f"ws_CO_{int(time.time())}",
                    'businessShortCode': self.account_number,
                    'callBackURL': f"{settings.SITE_URL}/payments/kcb/callback/",
                    'queueTimeOutURL': f"{settings.SITE_URL}/payments/kcb/timeout/"
                }
            elif self.account_type == 'bank':
                payload = {
                    'phoneNumber': phone_number,
                    'amount': str(int(amount)),
                    'accountReference': self.account_name or reference,
                    'transactionDesc': f'{self.business_name} - {plan_name}',
                    'merchantRequestID': reference,
                    'checkoutRequestID': f"ws_CO_{int(time.time())}",
                    'businessShortCode': self.account_number,
                    'callBackURL': f"{settings.SITE_URL}/payments/kcb/callback/",
                    'queueTimeOutURL': f"{settings.SITE_URL}/payments/kcb/timeout/"
                }
            else:
                return {'success': False, 'message': f'Unsupported account type: {self.account_type}'}
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            
            response = requests.post(
                f'{self.base_url}/payments/stk-push',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"STK Push initiated successfully: {reference}")
                return {
                    'success': True,
                    'transaction_id': reference,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'response_code': result.get('ResponseCode'),
                    'response_description': result.get('ResponseDescription'),
                    'customer_message': result.get('CustomerMessage'),
                    'raw_response': result
                }
            else:
                logger.error(f"STK Push failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Payment initiation failed: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error initiating STK Push: {str(e)}")
            return {'success': False, 'message': f'Payment error: {str(e)}'}
    
    def check_payment_status(self, checkout_request_id, merchant_request_id=None):
        """
        Check the status of a payment transaction
        
        Args:
            checkout_request_id (str): CheckoutRequestID from STK Push
            merchant_request_id (str): Optional MerchantRequestID
            
        Returns:
            dict: Payment status and details
        """
        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            payload = {
                'businessShortCode': self.account_number,
                'checkoutRequestID': checkout_request_id
            }
            
            if merchant_request_id:
                payload['merchantRequestID'] = merchant_request_id
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            
            response = requests.post(
                f'{self.base_url}/payments/stk-push/status',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': result.get('ResultCode'),
                    'status_description': result.get('ResultDesc'),
                    'transaction_id': result.get('MpesaReceiptNumber'),
                    'transaction_date': result.get('TransactionDate'),
                    'amount': result.get('Amount'),
                    'phone_number': result.get('PhoneNumber'),
                    'raw_response': result
                }
            else:
                logger.error(f"Payment status check failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Status check failed: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return {'success': False, 'message': f'Status check error: {str(e)}'}
    
    def reverse_transaction(self, transaction_id, amount, reason="Customer request"):
        """
        Reverse a completed transaction
        
        Args:
            transaction_id (str): M-Pesa transaction ID to reverse
            amount (float): Amount to reverse
            reason (str): Reason for reversal
            
        Returns:
            dict: Reversal status and details
        """
        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            payload = {
                'initiator': 'system',
                'securityCredential': self._get_security_credential(),
                'commandID': 'TransactionReversal',
                'transactionID': transaction_id,
                'amount': str(int(amount)),
                'receiverParty': self.account_number,
                'receiverIdentifierType': '4',  # Organization
                'resultURL': f"{settings.SITE_URL}/payments/kcb/reversal/result/",
                'queueTimeOutURL': f"{settings.SITE_URL}/payments/kcb/reversal/timeout/",
                'remarks': reason,
                'occasion': f'Reversal: {reason}'
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            
            response = requests.post(
                f'{self.base_url}/payments/reversal',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'conversation_id': result.get('ConversationID'),
                    'originator_conversation_id': result.get('OriginatorConversationID'),
                    'response_description': result.get('ResponseDescription'),
                    'raw_response': result
                }
            else:
                logger.error(f"Transaction reversal failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Reversal failed: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error reversing transaction: {str(e)}")
            return {'success': False, 'message': f'Reversal error: {str(e)}'}
    
    def get_account_balance(self):
        """
        Get account balance from KCB Buni
        
        Returns:
            dict: Account balance details
        """
        token = self.get_access_token()
        if not token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            payload = {
                'initiator': 'system',
                'securityCredential': self._get_security_credential(),
                'commandID': 'AccountBalance',
                'partyA': self.account_number,
                'identifierType': '4',  # Organization
                'resultURL': f"{settings.SITE_URL}/payments/kcb/balance/result/",
                'queueTimeOutURL': f"{settings.SITE_URL}/payments/kcb/balance/timeout/",
                'remarks': 'Balance inquiry'
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            
            response = requests.post(
                f'{self.base_url}/account/balance',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'conversation_id': result.get('ConversationID'),
                    'originator_conversation_id': result.get('OriginatorConversationID'),
                    'response_description': result.get('ResponseDescription'),
                    'raw_response': result
                }
            else:
                logger.error(f"Balance inquiry failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Balance inquiry failed: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {'success': False, 'message': f'Balance inquiry error: {str(e)}'}
    
    def validate_payment_credentials(self):
        """
        Validate that all required credentials and account details are present
        
        Returns:
            dict: Validation status and missing fields
        """
        missing_fields = []
        
        # Check global API credentials
        if not self.client_id:
            missing_fields.append('Global Client ID (settings.py)')
        if not self.client_secret:
            missing_fields.append('Global Client Secret (settings.py)')
        if not self.api_key:
            missing_fields.append('Global API Key (settings.py)')
        
        # Check station-specific account details
        if not self.account_type:
            missing_fields.append('Account Type')
        if not self.account_number:
            missing_fields.append('Account Number')
        
        # Validate account type
        if self.account_type not in ['paybill', 'till', 'bank']:
            missing_fields.append('Valid Account Type (paybill, till, or bank)')
        
        if missing_fields:
            return {
                'valid': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }
        
        # Test API connectivity (only if global credentials are present)
        if self.client_id and self.client_secret and self.api_key:
            token = self.get_access_token()
            if not token:
                return {
                    'valid': False,
                    'message': 'Failed to authenticate with KCB Buni API'
                }
        
        return {
            'valid': True,
            'message': 'All credentials and account details are valid, API is accessible'
        }
    
    def _get_security_credential(self):
        """
        Generate security credential for sensitive operations
        This is a placeholder - implement based on KCB Buni requirements
        """
        # This should be implemented based on KCB Buni's security requirements
        # Usually involves encrypting the password with their public key
        return base64.b64encode(f"{self.client_secret}".encode()).decode()
    
    def _generate_signature(self, data, timestamp):
        """
        Generate HMAC signature for API requests
        """
        message = f"{json.dumps(data, sort_keys=True)}{timestamp}"
        signature = hmac.new(
            self.client_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


# Utility functions for payment processing
def get_station_for_user_location(ip_address=None, mac_address=None):
    """
    Determine which station a user is connecting from
    This can be enhanced with more sophisticated logic
    """
    from mikrotik_integration.models import RouterConfig
    
    # Simple implementation - return the first active station
    # In production, this would use network topology or user location
    return RouterConfig.objects.filter(
        is_active=True,
        enable_payments=True
    ).first()


def format_phone_number(phone_number):
    """
    Format phone number to KCB Buni requirements (254XXXXXXXXX)
    """
    # Remove any non-digit characters
    phone_number = ''.join(filter(str.isdigit, phone_number))
    
    # Format to 254XXXXXXXXX
    if phone_number.startswith('0'):
        return '254' + phone_number[1:]
    elif phone_number.startswith('254'):
        return phone_number
    elif len(phone_number) == 9:
        return '254' + phone_number
    else:
        return phone_number


def calculate_transaction_fee(amount, station_config=None):
    """
    Calculate transaction fees based on amount and station configuration
    """
    # Basic fee calculation - can be enhanced with station-specific rates
    if amount <= 100:
        return 0
    elif amount <= 500:
        return 5
    elif amount <= 1000:
        return 10
    else:
        return 15