import os
import django
import json
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User, OTP

def test_auth_v1_flow():
    client = APIClient()
    email = "v1_test@example.com"
    password = "password123"
    
    print("\n=== STARTING AUTH V1 FLOW TEST ===\n")

    # 1. Cleanup
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
        print(f"[RESET] Deleted existing user {email}")

    # 2. Register
    print("\n[1] Registering User...")
    response = client.post('/api/v1/auth/register/', {
        'username': 'v1_tester',
        'email': email,
        'password': password,
        'full_name': 'V1 Tester',
        'role': 'ADULT'
    }, format='json')
    
    if response.status_code == 201:
        print("    SUCCESS: User registered.")
    else:
        print(f"    FAILED: {response.data}")
        return

    # 3. Fetch OTP
    otp = User.objects.get(email=email).otps.filter(purpose=OTP.Purpose.EMAIL_VERIFICATION).last()
    print(f"\n[2] Fetched OTP from DB: {otp.code}")

    # 4. Verify OTP
    print(f"\n[3] Verifying OTP...")
    response = client.post('/api/v1/auth/verify-otp/', {
        'email': email,
        'code': otp.code
    }, format='json')
    
    if response.status_code == 200:
        print("    SUCCESS: Email verified.")
    else:
        print(f"    FAILED: {response.data}")
        return

    # 5. Login
    print("\n[4] Logging in...")
    response = client.post('/api/v1/auth/login/', {
        'username': 'v1_tester',
        'password': password
    }, format='json')
    
    tokens = {}
    if response.status_code == 200:
        data = response.data
        if 'tokens' in data:
            tokens = data['tokens']
            print(f"    SUCCESS: Login Successful.")
            print(f"    Access Token: {tokens['access'][:20]}...")
            print(f"    Refresh Token: {tokens['refresh'][:20]}...")
        else:
            print("    FAILED: No tokens found in response.")
            return
    else:
        print(f"    FAILED: {response.data}")
        return

    # 6. Refresh Token
    print("\n[5] Refreshing Token...")
    response = client.post('/api/v1/auth/refresh-token/', {
        'refresh': tokens['refresh']
    }, format='json')
    
    if response.status_code == 200:
        print("    SUCCESS: Token refreshed.")
        print(f"    New Access Token: {response.data['access'][:20]}...")
    else:
        print(f"    FAILED: {response.data}")

    # 7. Logout
    print("\n[6] Logging Out...")
    response = client.post('/api/v1/auth/logout/', {
        'refresh': tokens['refresh']
    }, format='json')
    
    if response.status_code == 200:
        print("    SUCCESS: Logout successful (Token Blacklisted).")
    else:
        print(f"    FAILED: {response.data}")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_auth_v1_flow()
