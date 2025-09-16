"""
Mock KCB Buni API Client for Testing
Simulates KCB Buni API responses when sandbox is not accessible
"""

import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class MockKCBBuniClient:
    """
    Mock KCB Buni client that simulates API responses
    Use this when the real sandbox is not accessible for testing
    """
    
    def __init__(self):
        self.environment = "mock"
        self.base_url = "https://mock.kcb.local"
        self.client_id = "mock_client_id"
        self.client_secret = "mock_client_secret"
        self.shortcode = "174379"
        self.callback_url = "http://localhost:8000/payments/kcb/callback/"
        self.timeout_url = "http://localhost:8000/payments/kcb/timeout/"
        
        logger.info("Mock KCB Buni Client initialized for testing")
    
    def test_connection(self) -> Dict[str, Any]:
        """Mock connection test - always succeeds"""
        return {
            'success': True,
            'message': 'Mock KCB Buni API connection successful',
            'environment': self.environment,
            'base_url': self.base_url,
            'token_received': True
        }
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """Mock access token - returns a fake token"""
        mock_token = f"mock_token_{int(time.time())}"
        logger.info("Generated mock access token")
        return mock_token
    
    def initiate_stk_push(self, phone_number: str, amount: float, 
                         invoice_number: str, account_reference: str = None) -> Dict[str, Any]:
        """
        Mock STK Push initiation
        Simulates successful STK Push request
        """
        logger.info(f"Mock STK Push initiated for {phone_number}, Amount: KES {amount}")
        
        # Generate mock response similar to real KCB response
        mock_response = {
            'MerchantRequestID': f'mock_merchant_{uuid.uuid4().hex[:10]}',
            'CheckoutRequestID': f'ws_CO_mock_{uuid.uuid4().hex[:12]}',
            'ResponseCode': '0',
            'ResponseDescription': 'Success. Request accepted for processing',
            'CustomerMessage': 'Success. Request accepted for processing'
        }
        
        logger.info(f"Mock STK Push response: {mock_response['CheckoutRequestID']}")
        return mock_response
    
    def query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Mock STK Push status query
        Simulates transaction status response
        """
        logger.info(f"Mock STK status query for: {checkout_request_id}")
        
        # Simulate successful payment
        mock_response = {
            'ResponseCode': '0',
            'ResponseDescription': 'The service request has been accepted successfully',
            'MerchantRequestID': f'mock_merchant_{uuid.uuid4().hex[:10]}',
            'CheckoutRequestID': checkout_request_id,
            'ResultCode': '0',
            'ResultDesc': 'The service request is processed successfully.'
        }
        
        return mock_response
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number (same logic as real client)"""
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        if clean_number.startswith('254'):
            return clean_number
        elif clean_number.startswith('0'):
            return '254' + clean_number[1:]
        elif len(clean_number) == 9:
            return '254' + clean_number
        else:
            raise ValueError(f"Invalid phone number format: {phone_number}")
    
    def validate_callback_data(self, callback_data: dict) -> Tuple[bool, str]:
        """Mock callback validation - always validates successfully"""
        if isinstance(callback_data, dict):
            return True, "Valid mock callback data"
        return False, "Invalid callback data"
    
    def parse_callback_data(self, callback_data: dict) -> dict:
        """
        Mock callback parsing
        Returns parsed mock callback data
        """
        # Handle both real callback format and simplified test format
        if 'Body' in callback_data and 'stkCallback' in callback_data['Body']:
            # Real KCB format
            callback = callback_data['Body']['stkCallback']
            return {
                'checkout_request_id': callback.get('CheckoutRequestID'),
                'merchant_request_id': callback.get('MerchantRequestID'),
                'result_code': callback.get('ResultCode', 0),
                'result_desc': callback.get('ResultDesc', 'Success'),
                'callback_metadata': {}
            }
        else:
            # Simplified test format
            return {
                'checkout_request_id': callback_data.get('CheckoutRequestID', 'mock_checkout_123'),
                'merchant_request_id': callback_data.get('MerchantRequestID', 'mock_merchant_123'),
                'result_code': callback_data.get('ResultCode', 0),
                'result_desc': callback_data.get('ResultDesc', 'Mock successful payment'),
                'callback_metadata': {
                    'amount': callback_data.get('Amount', 0),
                    'mpesa_receipt_id': f'MOCK{uuid.uuid4().hex[:8].upper()}',
                    'phone_number': callback_data.get('PhoneNumber', '254700000000')
                }
            }


# Create mock client instance
mock_kcb_client = MockKCBBuniClient()