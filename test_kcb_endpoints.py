import requests
from requests.auth import HTTPBasicAuth
import socket

CLIENT_ID = "iKcMWAgpnujsb08fWMsmaZEIL0Ya"
CLIENT_SECRET = "OWEqLcPtwGI8wfNj71dYQ3fyksIa"

# Possible KCB Buni endpoints to test
endpoints = [
    "https://sandbox.kcbgroup.com/oauth/token",
    "https://api.kcbgroup.com/oauth/token",
    "https://sandbox-api.kcbgroup.com/oauth/token",
    "https://kcbgroup.com/oauth/token",
    "https://api.kcbbuni.com/oauth/token",
    "https://sandbox.kcbbuni.com/oauth/token",
    "https://developer.kcbgroup.com/oauth/token",
    "https://mpesa-api.kcbgroup.com/oauth/token",
]

def test_dns_resolution(hostname):
    """Test if hostname resolves"""
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False

def test_endpoint(url):
    """Test an OAuth endpoint"""
    print(f"\n🧪 Testing: {url}")
    
    # First check DNS resolution
    hostname = url.split('//')[1].split('/')[0]
    if not test_dns_resolution(hostname):
        print(f"❌ DNS: {hostname} does not resolve")
        return False
    else:
        print(f"✅ DNS: {hostname} resolves")
    
    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print(f"✅ SUCCESS: Token received!")
                print(f"   Token: {data['access_token'][:20]}...")
                return True
            else:
                print(f"⚠️  Response: {data}")
        elif response.status_code == 401:
            print(f"🔑 Endpoint exists but credentials invalid")
            return "auth_error"
        elif response.status_code == 404:
            print(f"❌ Endpoint not found")
        else:
            print(f"⚠️  Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectTimeout:
        print(f"⏱️  Connection timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return False

def main():
    print("🚀 KCB BUNI ENDPOINT DISCOVERY")
    print("=" * 50)
    print("Testing multiple possible endpoints...")
    
    working_endpoints = []
    auth_error_endpoints = []
    
    for url in endpoints:
        result = test_endpoint(url)
        if result == True:
            working_endpoints.append(url)
        elif result == "auth_error":
            auth_error_endpoints.append(url)
    
    print("\n" + "=" * 50)
    print("🔍 RESULTS SUMMARY")
    print("=" * 50)
    
    if working_endpoints:
        print("✅ WORKING ENDPOINTS (with tokens):")
        for endpoint in working_endpoints:
            print(f"   {endpoint}")
    
    if auth_error_endpoints:
        print("\n🔑 ENDPOINTS WITH AUTH ERRORS (exist but need valid creds):")
        for endpoint in auth_error_endpoints:
            print(f"   {endpoint}")
    
    if not working_endpoints and not auth_error_endpoints:
        print("❌ No working endpoints found")
        print("\n💡 Possible reasons:")
        print("   1. KCB Buni sandbox might be down")
        print("   2. Different API endpoints not tested")
        print("   3. Credentials might be invalid")
        print("   4. Special authentication required")
    else:
        if working_endpoints:
            print(f"\n🎉 Use this endpoint: {working_endpoints[0]}")

if __name__ == "__main__":
    main()