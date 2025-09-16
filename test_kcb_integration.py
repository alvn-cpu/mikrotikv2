#!/usr/bin/env python3
"""
Test script for the updated KCB Buni integration

Run this script to test the new station-specific account setup:
python test_kcb_integration.py
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_billing_system.settings')
django.setup()

from payments.kcb_buni_service import KCBBuniService
from mikrotik_integration.models import RouterConfig
from django.conf import settings

def test_global_credentials():
    """Test that global API credentials are configured"""
    print("=== Testing Global API Credentials ===")
    
    try:
        client_id = getattr(settings, 'KCB_BUNI_CLIENT_ID', '')
        client_secret = getattr(settings, 'KCB_BUNI_CLIENT_SECRET', '')
        api_key = getattr(settings, 'KCB_BUNI_API_KEY', '')
        base_url = getattr(settings, 'KCB_BUNI_BASE_URL', '')
        
        print(f"Base URL: {base_url}")
        print(f"Client ID: {'✓ Configured' if client_id else '✗ Missing'}")
        print(f"Client Secret: {'✓ Configured' if client_secret else '✗ Missing'}")
        print(f"API Key: {'✓ Configured' if api_key else '✗ Missing'}")
        
        if not all([client_id, client_secret, api_key]):
            print("\n❌ Global API credentials are not fully configured!")
            print("Please set KCB_BUNI_CLIENT_ID, KCB_BUNI_CLIENT_SECRET, and KCB_BUNI_API_KEY in your .env file")
            return False
        else:
            print("\n✅ Global API credentials are configured")
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking global credentials: {str(e)}")
        return False

def test_kcb_service_without_station():
    """Test KCB service initialization without station config"""
    print("\n=== Testing KCB Service (No Station Config) ===")
    
    try:
        service = KCBBuniService()
        print(f"Service initialized successfully")
        print(f"Account Type: {service.account_type}")
        print(f"Account Number: {service.account_number}")
        print(f"Account Name: {service.account_name}")
        print(f"Business Name: {service.business_name}")
        
        # Test validation
        validation_result = service.validate_payment_credentials()
        print(f"\nValidation Result: {validation_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing KCB service: {str(e)}")
        return False

def test_kcb_service_with_station():
    """Test KCB service with station configuration"""
    print("\n=== Testing KCB Service with Station Config ===")
    
    try:
        # Try to get a station or create a test one
        station = RouterConfig.objects.filter(is_active=True).first()
        
        if not station:
            print("No active stations found. Creating a test station...")
            station = RouterConfig.objects.create(
                name="Test Station",
                host="192.168.1.1",
                username="admin",
                password="test",
                business_name="Test WiFi Business",
                kcb_account_type="paybill",
                kcb_account_number="123456",
                account_name="Test Account",
                enable_payments=True,
                is_active=True
            )
            print(f"Created test station: {station.name}")
        else:
            print(f"Using existing station: {station.name}")
        
        # Initialize service with station config
        service = KCBBuniService(station_config=station)
        
        print(f"Service initialized with station: {station.name}")
        print(f"Account Type: {service.account_type}")
        print(f"Account Number: {service.account_number}")
        print(f"Account Name: {service.account_name}")
        print(f"Business Name: {service.business_name}")
        
        # Test validation
        validation_result = service.validate_payment_credentials()
        print(f"\nValidation Result: {validation_result}")
        
        if validation_result['valid']:
            print("✅ Station configuration is valid")
        else:
            print(f"❌ Station configuration issue: {validation_result['message']}")
        
        return validation_result['valid']
        
    except Exception as e:
        print(f"❌ Error testing with station config: {str(e)}")
        return False

def test_database_migration():
    """Test that the new database fields exist"""
    print("\n=== Testing Database Migration ===")
    
    try:
        # Check if new fields exist on RouterConfig model
        station = RouterConfig.objects.first()
        if not station:
            print("No stations in database to test")
            return True
            
        # Try to access new fields
        account_type = getattr(station, 'kcb_account_type', None)
        account_number = getattr(station, 'kcb_account_number', None)  
        account_name = getattr(station, 'account_name', None)
        
        print(f"New fields found:")
        print(f"  kcb_account_type: {'✓' if hasattr(station, 'kcb_account_type') else '✗'}")
        print(f"  kcb_account_number: {'✓' if hasattr(station, 'kcb_account_number') else '✗'}")
        print(f"  account_name: {'✓' if hasattr(station, 'account_name') else '✗'}")
        
        if all(hasattr(station, field) for field in ['kcb_account_type', 'kcb_account_number', 'account_name']):
            print("✅ Database migration completed successfully")
            return True
        else:
            print("❌ Database migration may not be complete. Run: python manage.py migrate")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database migration: {str(e)}")
        return False

def test_station_creation():
    """Test creating a new station with the new fields"""
    print("\n=== Testing Station Creation ===")
    
    try:
        # Create a test station with new fields
        station = RouterConfig.objects.create(
            name="Integration Test Station",
            host="192.168.100.1",
            username="testuser",
            password="testpass",
            business_name="Integration Test Business",
            kcb_account_type="till",
            kcb_account_number="987654",
            account_name="Integration Test Account",
            enable_payments=True,
            is_active=True
        )
        
        print(f"✅ Successfully created station: {station.name}")
        print(f"   Account Type: {station.kcb_account_type}")
        print(f"   Account Number: {station.kcb_account_number}")
        print(f"   Account Name: {station.account_name}")
        
        # Clean up test station
        station.delete()
        print("   Test station cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test station: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("KCB Buni Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Global Credentials", test_global_credentials),
        ("Database Migration", test_database_migration),
        ("Station Creation", test_station_creation),
        ("KCB Service (No Station)", test_kcb_service_without_station),
        ("KCB Service (With Station)", test_kcb_service_with_station),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 50)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The KCB integration update is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")
    
    print("\nNext Steps:")
    print("1. If any tests failed, fix the issues and run the tests again")
    print("2. Update existing stations with their KCB account details")
    print("3. Test actual payment flow in a controlled environment")
    print("4. Monitor logs for any issues in production")

if __name__ == "__main__":
    main()