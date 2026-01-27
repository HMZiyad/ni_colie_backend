import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User, OTP

def test_robustness():
    client = APIClient()
    email = "robust_test@example.com"
    password = "password123"
    
    print("\n=== STARTING ROBUSTNESS TEST ===\n")

    # 1. Cleanup
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
    
    initial_user_count = User.objects.count()

    # 2. Register (Should FAIL because email fails locaally)
    print("\n[1] Registering User (Expect Failure)...")
    response = client.post('/api/v1/auth/register/', {
        'username': 'robust_tester',
        'email': email,
        'password': password,
        'full_name': 'Robust Tester',
        'role': 'ADULT'
    }, format='json')
    
    if response.status_code == 500:
        print("    SUCCESS: Registration failed as expected (HTTP 500).")
        print(f"    Error: {response.data['error']}")
    elif response.status_code == 201:
        print("    FAILURE: Registration succeeded unexpectedly!")
    else:
        print(f"    FAILURE: Unexpected status code {response.status_code}")
        print(response.data)

    # 3. Verify Rollback
    final_user_count = User.objects.count()
    if final_user_count == initial_user_count:
        print(f"    SUCCESS: User count remained at {initial_user_count} (Rollback worked).")
    else:
        print(f"    FAILURE: User count increased to {final_user_count} (Zombie user created).")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_robustness()
