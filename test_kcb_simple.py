#!/usr/bin/env python3
"""
Simple KCB Buni Integration Test
Tests basic connectivity and token management
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_billing_system.settings')
django.setup()

from payments.services.kcb_client import kcb_client, KCBBuniError

def test_connection():
    """Test KCB API connection"""
    print("🧪 Testing KCB Buni Connection")
    print("=" * 40)
    
    try:
        print(f"Base URL: {kcb_client.base_url}")
        print(f"Environment: {kcb_client.environment}")
        print(f"Client ID: {kcb_client.client_id[:10]}...")  # Show first 10 chars only
        
        result = kcb_client.test_connection()
        
        if result['success']:
            print("✅ Connection successful!")
            print(f"Environment: {result['environment']}")
            print(f"Base URL: {result['base_url']}")
            print(f"Token received: {result['token_received']}")
            return True
        else:
            print("❌ Connection failed!")
            print(f"Error: {result['message']}")
            return False
    
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def test_token():
    """Test token management"""
    print("\n🔑 Testing Token Management")
    print("=" * 40)
    
    try:
        # Get token
        token = kcb_client.get_access_token()
        print(f"✅ Token obtained: {token[:20]}...")
        
        # Test cached token
        token2 = kcb_client.get_access_token()
        if token == token2:
            print("✅ Token caching works!")
        else:
            print("⚠️ Token caching issue")
        
        return True
    
    except Exception as e:
        print(f"❌ Token error: {str(e)}")
        return False

def main():
    print("🚀 KCB BUNI INTEGRATION TEST")
    print("Testing sandbox environment...")
    print()
    
    tests_passed = 0
    total_tests = 2
    
    if test_connection():
        tests_passed += 1
    
    if test_token():
        tests_passed += 1
    
    print(f"\n📊 RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! KCB integration is working.")
        print("\n📝 Next steps:")
        print("1. Test STK Push with a registered phone number")
        print("2. Integrate with your WiFi purchase flow")
        print("3. Test complete payment workflow")
    else:
        print("⚠️ Some tests failed. Check configuration.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")