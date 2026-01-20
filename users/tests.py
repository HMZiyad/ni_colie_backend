from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import OTP, InmateProfile
from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.verify_otp_url = reverse('verify_otp')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'full_name': 'Test User',
            'role': 'ADULT'
        }

    def test_registration_success(self):
        """Test that a valid user can register."""
        print("\n[TEST] test_registration_success: Starting...")
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        self.assertTrue(OTP.objects.filter(user__email='test@example.com').exists())
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)  # Should be inactive until verified
        print("   -> Registration Successful. OTP Generated.")

    @patch('users.views.send_otp_email')
    def test_registration_rollback_on_email_failure(self, mock_send_email):
        """Test that user is NOT created if email sending fails."""
        print("\n[TEST] test_registration_rollback_on_email_failure: Starting...")
        mock_send_email.side_effect = Exception("SMTP Error")
        
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(User.objects.filter(email='test@example.com').exists())
        print("   -> Rollback Successful. User not created on email failure.")

    def test_registration_duplicate_email(self):
        """Test that registering with an existing email fails."""
        print("\n[TEST] test_registration_duplicate_email: Starting...")
        # First registration
        self.client.post(self.register_url, self.user_data)
        
        # Second registration with same email but different username
        data = self.user_data.copy()
        data['username'] = 'otheruser'
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        print("   -> Duplicate Email Rejected as expected.")

    def test_otp_verification_success(self):
        """Test valid OTP verification activates user."""
        print("\n[TEST] test_otp_verification_success: Starting...")
        # Register
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email='test@example.com')
        otp = user.otps.first()

        # Verify
        response = self.client.post(self.verify_otp_url, {
            'email': self.user_data['email'],
            'code': otp.code
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        print("   -> OTP Verification Successful. User Activated.")

    def test_otp_verification_failed_expired(self):
        """Test expired OTP is rejected."""
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email='test@example.com')
        otp = user.otps.first()
        
        # Expire the OTP manually
        otp.created_at = timezone.now() - timedelta(minutes=5)
        otp.save()

        response = self.client.post(self.verify_otp_url, {
            'email': self.user_data['email'],
            'code': otp.code
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data))
        print("   -> Expired OTP Correctly Rejected.")

    def test_login_success(self):
        """Test login returns JWT tokens."""
        print("\n[TEST] test_login_success: Starting...")
        # Register & Verify manually
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()

        response = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        print("   -> Login Successful. JWT Tokens Received.")

    def test_logout_success(self):
        """Test logout blacklists refresh token."""
        # Create user & login manually to get tokens
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        login_resp = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        refresh_token = login_resp.data['tokens']['refresh']

    def test_resend_otp(self):
        """Test OTP resend functionality."""
        print("\n[TEST] test_resend_otp: Starting...")
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email='test@example.com')
        old_otp_code = user.otps.last().code
        
        # Resend
        response = self.client.post(reverse('resend_otp'), {'email': self.user_data['email']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new code
        new_otp_code = user.otps.last().code
        self.assertNotEqual(old_otp_code, new_otp_code)
        print("   -> OTP Resend Successful. New Code Generated.")

    def test_forgot_and_reset_password(self):
        """Test forgot password and reset password flow."""
        print("\n[TEST] test_forgot_and_reset_password: Starting...")
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        old_hash = user.password

        # 1. Forgot Password
        response = self.client.post(reverse('forgot_password'), {'email': self.user_data['email']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        otp = user.otps.filter(purpose=OTP.Purpose.PASSWORD_RESET).last()
        print("   -> Forgot Password: OTP Sent.")

        # 2. Reset Password
        new_pass = "brandnewpass123"
        response = self.client.post(reverse('reset_password'), {
            'email': self.user_data['email'],
            'code': otp.code,
            'new_password': new_pass
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_pass))
        self.assertNotEqual(user.password, old_hash)
        print("   -> Password Reset Successful.")

    def test_token_refresh(self):
        """Test that refresh token generates new access token."""
        print("\n[TEST] test_token_refresh: Starting...")
        user = User.objects.create_user(**self.user_data)
        user.is_active = True
        user.save()
        
        # Login
        login_resp = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        refresh = login_resp.data['tokens']['refresh']
        old_access = login_resp.data['tokens']['access']

        # Refresh
        response = self.client.post(reverse('token_refresh'), {'refresh': refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotEqual(response.data['access'], old_access)
        print("   -> Token Refresh Successful.")


class RoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')

    def test_role_assignment(self):
        """Test distinct role assignment."""
        print("\n[TEST] test_role_assignment: Starting...")
        roles = ['KID', 'TEEN', 'ADULT', 'ADMIN']
        for role in roles:
            data = {
                'username': f'test_{role}',
                'email': f'test_{role}@example.com',
                'password': 'password123',
                'full_name': f'Test {role}',
                'role': role
            }
            response = self.client.post(self.register_url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed for {role}")
            user = User.objects.get(username=f'test_{role}')
            self.assertEqual(user.role, role)
        print("   -> All Roles Assigned Correctly.")

    def test_inmate_profile_creation(self):
        """Test that registering as INMATE creates a profile."""
        print("\n[TEST] test_inmate_profile_creation: Starting...")
        data = {
            'username': 'inmate_user',
            'email': 'inmate@example.com',
            'password': 'password123',
            'full_name': 'Inmate User',
            'role': 'INMATE',
            'inmate_profile': {
                'age': 30,
                'highest_education': 'High School',
                'incarceration_status': 'Released',
                'training_completed': 'Carpentry',
                'priorities': 'Job'
            }
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='inmate_user')
        self.assertTrue(hasattr(user, 'inmate_profile'))
        self.assertEqual(user.inmate_profile.age, 30)

class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profile_test',
            email='profile@example.com',
            password='password123',
            role='ADULT'
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.profile_url = reverse('user_profile')

    def test_get_profile(self):
        """Test retrieving user profile."""
        print("\n[TEST] test_get_profile: Starting...")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profile_test')
        print("   -> Profile Retrieval Successful.")

    def test_update_profile(self):
        """Test updating generic profile fields."""
        print("\n[TEST] test_update_generic_profile: Starting...")
        data = {'full_name': 'New Name', 'phone_number': '1234567890'}
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'New Name')
        print("   -> Profile Update Successful.")

    def test_update_settings(self):
        """Test updating user settings JSON."""
        print("\n[TEST] test_update_settings: Starting...")
        settings_url = reverse('user_settings')
        data = {'settings': {'theme': 'dark', 'notifications': True}}
        response = self.client.put(settings_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.settings['theme'], 'dark')
        print("   -> Settings Update Successful.")

    def test_update_favorite_roles(self):
        """Test updating favorite roles list."""
        print("\n[TEST] test_update_favorite_roles: Starting...")
        url = reverse('user_favorite_roles')
        data = {'favorite_roles': ['Chef', 'Doctor']}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(len(self.user.favorite_roles), 2)
        print("   -> Favorite Roles Update Successful.")

    def test_account_deactivation(self):
        """Test soft deleting account."""
        print("\n[TEST] test_account_deactivation: Starting...")
        response = self.client.delete(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        print("   -> Account Deactivation Successful.")

