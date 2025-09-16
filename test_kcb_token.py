import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "iKcMWAgpnujsb08fWMsmaZEIL0Ya"
CLIENT_SECRET = "OWEqLcPtwGI8wfNj71dYQ3fyksIa"

url = "https://sandbox.kcbgroup.com/oauth/token"

print("🚀 Requesting access token from KCB Buni Sandbox...")

try:
    response = requests.post(
        url,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=10
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Access Token:", token)
    else:
        print("❌ Error:", response.status_code, response.text)

except Exception as e:
    print("⚠️ Exception:", str(e))