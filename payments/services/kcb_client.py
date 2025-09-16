"""
KCB Buni API Client - Professional Implementation
Handles token management, error handling, and API communication
"""

import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Any, Optional, Tuple
import json
import time
from django.utils import timezone

logger = logging.getLogger(__name__)


class KCBBuniError(Exception):
    """Custom exception for KCB Buni API errors"""
    
    def __init__(self, message: str, error_code: str = None, response_data: dict = None):
        self.error_code = error_code
        self.response_data = response_data or {}
        super().__init__(message)


class KCBBuniClient:
    """
    Professional KCB Buni API Client with advanced features:
    - Token caching and auto-refresh
    - Comprehensive error handling
    - Request/response logging
    - Retry mechanisms
    - Environment management (sandbox/production)
    """
    
    def __init__(self):
        self.base_url = settings.KCB_BUNI_BASE_URL
        self.client_id = settings.KCB_BUNI_CLIENT_ID
        self.client_secret = settings.KCB_BUNI_CLIENT_SECRET
        self.shortcode = settings.KCB_BUNI_SHORTCODE
        self.callback_url = settings.KCB_BUNI_CALLBACK_URL
        self.timeout_url = settings.KCB_BUNI_TIMEOUT_URL
        self.environment = getattr(settings, 'KCB_BUNI_ENVIRONMENT', 'sandbox')
        
        # Token management
        self.token_cache_key = 'kcb_buni_access_token'
        self.token_expiry_buffer = 300  # 5 minutes buffer
        
        # Request configuration
        self.session = requests.Session()
        self.session.timeout = 30
        
        logger.info(f"KCB Buni Client initialized for {self.environment} environment")
    
    def _log_request(self, method: str, url: str, data: dict = None, response: requests.Response = None):
        """Log API requests and responses for debugging"""
        request_id = f"req_{int(time.time())}"
        
        logger.info(f"[{request_id}] {method} {url}")
        if data and self.environment == 'sandbox':
            # Only log request data in sandbox for security
            logger.info(f"[{request_id}] Request: {json.dumps(data, indent=2)}")
        
        if response:
            logger.info(f"[{request_id}] Response Status: {response.status_code}")
            if response.content and self.environment == 'sandbox':
                try:
                    logger.info(f"[{request_id}] Response: {json.dumps(response.json(), indent=2)}")
                except:
                    logger.info(f"[{request_id}] Response: {response.text}")
    
    def _handle_response_error(self, response: requests.Response, context: str = "") -> None:
        """Handle HTTP response errors with detailed logging"""
        if response.status_code == 200:
            return
            
        error_msg = f"KCB Buni API Error ({context}): {response.status_code}"
        
        try:
            error_data = response.json()
            error_msg += f" - {error_data.get('error_description', error_data.get('message', 'Unknown error'))}"
            
            raise KCBBuniError(
                message=error_msg,
                error_code=error_data.get('error', str(response.status_code)),
                response_data=error_data
            )
        except json.JSONDecodeError:
            error_msg += f" - {response.text}"
            raise KCBBuniError(message=error_msg, error_code=str(response.status_code))
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get cached access token or fetch new one
        
        Args:
            force_refresh: Force token refresh even if cached token exists
            
        Returns:
            str: Valid access token
            
        Raises:
            KCBBuniError: If token request fails
        """
        if not force_refresh:
            # Try to get cached token
            cached_token = cache.get(self.token_cache_key)
            if cached_token:
                logger.debug("Using cached access token")
                return cached_token
        
        logger.info("Requesting new access token from KCB Buni")
        
        # Request new token
        url = f"{self.base_url}/oauth/token"
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = self.session.post(
                url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            self._log_request("POST", url, data, response)
            self._handle_response_error(response, "Token Request")
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            
            if not access_token:
                raise KCBBuniError("No access token in response", response_data=token_data)
            
            # Cache token with expiry buffer
            cache_timeout = expires_in - self.token_expiry_buffer
            cache.set(self.token_cache_key, access_token, timeout=cache_timeout)
            
            logger.info(f"Access token cached for {cache_timeout} seconds")
            return access_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error requesting access token: {str(e)}"
            logger.error(error_msg)
            raise KCBBuniError(error_msg)
    
    def _make_authenticated_request(self, method: str, endpoint: str, data: dict = None, 
                                  retries: int = 1) -> dict:
        """
        Make authenticated request to KCB Buni API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request payload
            retries: Number of retries for token refresh
            
        Returns:
            dict: API response data
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise KCBBuniError(f"Unsupported HTTP method: {method}")
            
            self._log_request(method, url, data, response)
            
            # Handle token expiry - retry with new token
            if response.status_code == 401 and retries > 0:
                logger.warning("Token expired, refreshing and retrying request")
                cache.delete(self.token_cache_key)  # Clear cached token
                return self._make_authenticated_request(method, endpoint, data, retries - 1)
            
            self._handle_response_error(response, f"{method} {endpoint}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error in authenticated request: {str(e)}"
            logger.error(error_msg)
            raise KCBBuniError(error_msg)
    
    def initiate_stk_push(self, phone_number: str, amount: float, 
                         invoice_number: str, account_reference: str = None) -> dict:
        """
        Initiate STK Push payment request
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Payment amount
            invoice_number: Unique invoice/transaction ID
            account_reference: Optional account reference
            
        Returns:
            dict: STK Push response data
        """
        logger.info(f"Initiating STK Push for {phone_number}, Amount: KES {amount}")
        
        # Validate and format phone number
        formatted_phone = self._format_phone_number(phone_number)
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": self._generate_password(),
            "Timestamp": self._get_timestamp(),
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),  # Convert to string and remove decimals
            "PartyA": formatted_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference or invoice_number,
            "TransactionDesc": f"WiFi Plan Payment - {invoice_number}"
        }
        
        try:
            response_data = self._make_authenticated_request(
                "POST", 
                "/mpesa-express/v1/stkpush", 
                payload
            )
            
            logger.info(f"STK Push initiated successfully. CheckoutRequestID: {response_data.get('CheckoutRequestID')}")
            return response_data
            
        except KCBBuniError as e:
            logger.error(f"STK Push initiation failed: {str(e)}")
            raise
    
    def query_stk_status(self, checkout_request_id: str) -> dict:
        """
        Query STK Push transaction status
        
        Args:
            checkout_request_id: Checkout request ID from STK Push response
            
        Returns:
            dict: Transaction status response
        """
        logger.info(f"Querying STK status for CheckoutRequestID: {checkout_request_id}")
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": self._generate_password(),
            "Timestamp": self._get_timestamp(),
            "CheckoutRequestID": checkout_request_id
        }
        
        try:
            response_data = self._make_authenticated_request(
                "POST",
                "/mpesa-express/v1/stkpushquery",
                payload
            )
            
            logger.info(f"STK status query completed: {response_data.get('ResultDesc', 'Unknown')}")
            return response_data
            
        except KCBBuniError as e:
            logger.error(f"STK status query failed: {str(e)}")
            raise
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to KCB Buni standard (254XXXXXXXXX)
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            str: Formatted phone number
        """
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different formats
        if clean_number.startswith('254'):
            return clean_number
        elif clean_number.startswith('0'):
            return '254' + clean_number[1:]
        elif len(clean_number) == 9:
            return '254' + clean_number
        else:
            raise KCBBuniError(f"Invalid phone number format: {phone_number}")
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for API requests"""
        return timezone.now().strftime('%Y%m%d%H%M%S')
    
    def _generate_password(self) -> str:
        """Generate password for STK Push (Base64 encoded)"""
        import base64
        timestamp = self._get_timestamp()
        # For sandbox, use test passkey
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"  # Sandbox passkey
        
        password_string = f"{self.shortcode}{passkey}{timestamp}"
        password_bytes = password_string.encode('utf-8')
        return base64.b64encode(password_bytes).decode('utf-8')
    
    def validate_callback_data(self, callback_data: dict) -> Tuple[bool, str]:
        """
        Validate callback data from KCB Buni
        
        Args:
            callback_data: Raw callback data
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        required_fields = ['Body', 'stkCallback']
        
        try:
            # Check for required structure
            for field in required_fields:
                if field not in callback_data:
                    return False, f"Missing required field: {field}"
            
            callback = callback_data['Body']['stkCallback']
            
            # Check for required callback fields
            if 'CheckoutRequestID' not in callback:
                return False, "Missing CheckoutRequestID in callback"
                
            if 'ResultCode' not in callback:
                return False, "Missing ResultCode in callback"
            
            return True, "Valid callback data"
            
        except (KeyError, TypeError) as e:
            return False, f"Invalid callback structure: {str(e)}"
    
    def parse_callback_data(self, callback_data: dict) -> dict:
        """
        Parse and extract relevant data from callback
        
        Args:
            callback_data: Raw callback data
            
        Returns:
            dict: Parsed callback data
        """
        callback = callback_data['Body']['stkCallback']
        
        parsed_data = {
            'checkout_request_id': callback.get('CheckoutRequestID'),
            'merchant_request_id': callback.get('MerchantRequestID'),
            'result_code': callback.get('ResultCode'),
            'result_desc': callback.get('ResultDesc'),
            'callback_metadata': {}
        }
        
        # Extract metadata if payment was successful
        if callback.get('CallbackMetadata') and callback['CallbackMetadata'].get('Item'):
            for item in callback['CallbackMetadata']['Item']:
                name = item.get('Name', '').lower()
                value = item.get('Value')
                
                if name == 'amount':
                    parsed_data['callback_metadata']['amount'] = float(value)
                elif name == 'mpesareceiptid':
                    parsed_data['callback_metadata']['mpesa_receipt_id'] = value
                elif name == 'transactiondate':
                    parsed_data['callback_metadata']['transaction_date'] = value
                elif name == 'phonenumber':
                    parsed_data['callback_metadata']['phone_number'] = value
        
        return parsed_data
    
    def test_connection(self) -> dict:
        """
        Test connection to KCB Buni API
        
        Returns:
            dict: Connection test results
        """
        try:
            access_token = self.get_access_token()
            
            return {
                'success': True,
                'message': 'Successfully connected to KCB Buni API',
                'environment': self.environment,
                'base_url': self.base_url,
                'token_received': bool(access_token)
            }
            
        except KCBBuniError as e:
            return {
                'success': False,
                'message': str(e),
                'environment': self.environment,
                'base_url': self.base_url,
                'error_code': e.error_code
            }


# Singleton instance for easy import
kcb_client = KCBBuniClient()