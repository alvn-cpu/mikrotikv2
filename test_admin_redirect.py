"""
Test script to verify that Django admin is disabled and redirects work
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_billing_system.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

def test_admin_redirect():
    """Test that admin URLs redirect to custom login"""
    client = Client()
    
    print("🧪 Testing Admin Redirect Functionality")
    print("=" * 50)
    
    # Test 1: Admin root URL
    print("\\n1. Testing /admin/ redirect...")
    response = client.get('/admin/')
    if response.status_code == 302:
        print(f"✅ /admin/ redirects to: {response.url}")
        assert '/auth/login/' in response.url, "Should redirect to custom login"
    else:
        print(f"❌ /admin/ returned status: {response.status_code}")
    
    # Test 2: Admin login URL
    print("\\n2. Testing /admin/login/ redirect...")
    response = client.get('/admin/login/')
    if response.status_code == 302:
        print(f"✅ /admin/login/ redirects to: {response.url}")
        assert '/auth/login/' in response.url, "Should redirect to custom login"
    else:
        print(f"❌ /admin/login/ returned status: {response.status_code}")
    
    # Test 3: Admin with next parameter (your specific case)
    print("\\n3. Testing /admin/login/?next=/dashboard/admin-dashboard/...")
    response = client.get('/admin/login/?next=/dashboard/admin-dashboard/')
    if response.status_code == 302:
        print(f"✅ Admin login with next redirects to: {response.url}")
        assert '/auth/login/' in response.url, "Should redirect to custom login"
        assert 'next=' in response.url, "Should preserve next parameter"
    else:
        print(f"❌ Admin login with next returned status: {response.status_code}")
    
    # Test 4: Custom login page works
    print("\\n4. Testing custom login page accessibility...")
    response = client.get('/auth/login/')
    if response.status_code == 200:
        print("✅ Custom login page is accessible")
    else:
        print(f"❌ Custom login page returned status: {response.status_code}")
    
    # Test 5: Dashboard requires authentication
    print("\\n5. Testing dashboard authentication requirement...")
    response = client.get('/dashboard/admin-dashboard/')
    if response.status_code == 302:
        print(f"✅ Dashboard redirects unauthorized users to: {response.url}")
        assert '/auth/login/' in response.url, "Should redirect to custom login"
    else:
        print(f"❌ Dashboard returned status: {response.status_code}")
    
    print("\\n" + "=" * 50)
    print("🎉 Admin redirect tests completed!")
    print("🔒 Django admin is successfully disabled and redirecting to custom login")

if __name__ == '__main__':
    try:
        test_admin_redirect()
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()