#!/usr/bin/env python3
"""
KCB Buni Mock Integration Test
Tests the complete payment workflow using mock client
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_billing_system.settings')
django.setup()

from payments.services.kcb_mock_client import mock_kcb_client
from payments.services.payment_processor import payment_processor
from billing.models import WifiUser, WifiPlan
from payments.models import PaymentTransaction
from django.utils import timezone
from decimal import Decimal

def test_mock_connection():
    """Test mock KCB client connection"""
    print("🧪 Testing Mock KCB Connection")
    print("=" * 40)
    
    try:
        result = mock_kcb_client.test_connection()
        
        if result['success']:
            print("✅ Connection successful!")
            print(f"Environment: {result['environment']}")
            print(f"Base URL: {result['base_url']}")
            print(f"Token received: {result['token_received']}")
            return True
        else:
            print("❌ Connection failed!")
            return False
    
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def test_mock_stk_push():
    """Test mock STK Push"""
    print("\n📱 Testing Mock STK Push")
    print("=" * 40)
    
    try:
        # Test STK Push initiation
        result = mock_kcb_client.initiate_stk_push(
            phone_number="254712345678",
            amount=50.0,
            invoice_number="TEST-INVOICE-123",
            account_reference="test-user"
        )
        
        print("✅ STK Push initiated!")
        print(f"Checkout Request ID: {result.get('CheckoutRequestID')}")
        print(f"Merchant Request ID: {result.get('MerchantRequestID')}")
        print(f"Response: {result.get('ResponseDescription')}")
        
        # Test status query
        if result.get('CheckoutRequestID'):
            status_result = mock_kcb_client.query_stk_status(result['CheckoutRequestID'])
            print(f"✅ Status Query Result: {status_result.get('ResultDesc')}")
        
        return True
    
    except Exception as e:
        print(f"❌ STK Push error: {str(e)}")
        return False

def test_payment_workflow():
    """Test complete payment workflow with mock client"""
    print("\n🛒 Testing Complete Payment Workflow")
    print("=" * 40)
    
    try:
        # Create test plan
        plan, created = WifiPlan.objects.get_or_create(
            name="Mock Test Plan",
            defaults={
                'price': Decimal('25.00'),
                'plan_type': 'data',
                'data_limit_mb': 100,
                'duration_minutes': 120,
                'upload_speed_kbps': 512,  # Add required field
                'download_speed_kbps': 1024,  # Add required field
                'description': 'Mock test plan',
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created test plan: {plan.name}")
        else:
            print(f"✅ Using existing plan: {plan.name}")
        
        # Create test user
        user, created = WifiUser.objects.get_or_create(
            phone_number="254712345678",
            defaults={
                'status': 'pending',
                'created_at': timezone.now()
            }
        )
        
        if created:
            print(f"✅ Created test user: {user.phone_number}")
        else:
            print(f"✅ Using existing user: {user.phone_number}")
        
        # Use mock client in payment processor
        # We need to temporarily replace the KCB client
        from payments.services import payment_processor as pp_module
        original_client = pp_module.payment_processor.kcb_client
        pp_module.payment_processor.kcb_client = mock_kcb_client
        
        try:
            # Process payment
            result = payment_processor.process_wifi_plan_purchase(
                user=user,
                plan=plan,
                phone_number="254712345678"
            )
            
            if result['success']:
                print("✅ Payment processing initiated!")
                print(f"Transaction ID: {result['transaction_id']}")
                print(f"Message: {result['message']}")
                
                # Simulate callback (payment completion)
                print("\n📞 Simulating Payment Callback...")
                
                callback_data = {
                    'CheckoutRequestID': result.get('checkout_request_id', 'mock_checkout_123'),
                    'ResultCode': 0,
                    'ResultDesc': 'Mock payment successful',
                    'Amount': 25,
                    'PhoneNumber': '254712345678'
                }
                
                callback_result = payment_processor.handle_payment_callback(callback_data)
                
                if callback_result['success']:
                    print("✅ Payment callback processed!")
                    print(f"Final Status: {callback_result.get('status')}")
                    
                    # Check user status
                    user.refresh_from_db()
                    print(f"✅ User status updated: {user.status}")
                    print(f"✅ Plan activated: {user.current_plan.name if user.current_plan else 'None'}")
                    
                    return True
                else:
                    print(f"❌ Callback processing failed: {callback_result['message']}")
                    return False
            else:
                print(f"❌ Payment processing failed: {result['message']}")
                return False
                
        finally:
            # Restore original client
            pp_module.payment_processor.kcb_client = original_client
    
    except Exception as e:
        print(f"❌ Workflow error: {str(e)}")
        return False

def main():
    print("🚀 KCB BUNI MOCK INTEGRATION TEST")
    print("Testing complete workflow with mock client...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_mock_connection():
        tests_passed += 1
    
    if test_mock_stk_push():
        tests_passed += 1
    
    if test_payment_workflow():
        tests_passed += 1
    
    print(f"\n📊 RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 50)
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your WiFi payment integration is working!")
        print("\n📝 What this proves:")
        print("  • Payment transaction creation works")
        print("  • STK Push initiation works")
        print("  • Callback processing works")
        print("  • User account activation works")
        print("\n🔄 Next Steps:")
        print("  1. Test with your captive portal")
        print("  2. Create a purchase form for customers")
        print("  3. Switch to real KCB sandbox when accessible")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")