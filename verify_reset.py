import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, OTP
from rest_framework.test import APIClient

def test_reset_flow():
    client = APIClient()
    email = "reset_test@example.com"
    password = "oldpassword123"
    new_password = "newpassword456"

    # 1. Create User
    print(f"1. Creating user {email}...")
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
    
    user = User.objects.create_user(username="reset_tester", email=email, password=password)
    print("   User created.")

    # 2. Request OTP
    print("2. Requesting Password Reset OTP...")
    response = client.post('/api/auth/forgot-password/', {'email': email}, format='json')
    if response.status_code != 200:
        print(f"   FAILED: {response.data}")
        return
    print("   OTP sent.")

    # 3. Fetch OTP from DB
    otp = User.objects.get(email=email).otps.filter(purpose=OTP.Purpose.PASSWORD_RESET).last()
    print(f"   Fetched OTP from DB: {otp.code}")

    # 4. Reset Password
    print("3. Resetting Password...")
    data = {
        'email': email,
        'code': otp.code,
        'new_password': new_password
    }
    response = client.post('/api/auth/reset-password/', data, format='json')
    if response.status_code != 200:
        print(f"   FAILED: {response.data}")
        return
    print("   Password reset successful.")

    # 5. Verify Login with New Password
    print("4. Verifying Login with NEW password...")
    response = client.post('/api/auth/login/', {'username': 'reset_tester', 'password': new_password}, format='json')
    if response.status_code == 200:
        print("   SUCCESS: Login with new password worked.")
    else:
        print(f"   FAILED: Login failed. {response.data}")

if __name__ == "__main__":
    test_reset_flow()
