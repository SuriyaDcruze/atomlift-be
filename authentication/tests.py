from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import OTP

User = get_user_model()


class MobileAuthAPITestCase(APITestCase):
    def setUp(self):
        # Create employee group
        self.employee_group = Group.objects.create(name='Employees')
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890'
        )
        
        # Add user to employee group
        self.user.groups.add(self.employee_group)
        
        # Create user profile
        self.user.profile.branch = 'Test Branch'
        self.user.profile.designation = 'Test Role'
        self.user.profile.save()

    def test_generate_otp_with_email(self):
        """Test OTP generation with email"""
        url = '/auth/api/mobile/generate-otp/'
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['otp_type'], 'email')
        
        # Check OTP was created
        otp = OTP.objects.filter(user=self.user, otp_type='email').first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.otp_code), 6)

    def test_generate_otp_with_phone(self):
        """Test OTP generation with phone number"""
        url = '/auth/api/mobile/generate-otp/'
        data = {'phone_number': '+1234567890'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['otp_type'], 'phone')

    def test_generate_otp_non_employee(self):
        """Test OTP generation fails for non-employee users"""
        # Remove user from employee group
        self.user.groups.clear()
        
        url = '/auth/api/mobile/generate-otp/'
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Access denied', response.data['error'])

    def test_verify_otp_and_login(self):
        """Test OTP verification and login"""
        # Generate OTP first
        otp = OTP.generate_otp(self.user, 'email', 'test@example.com')
        
        url = '/auth/api/mobile/verify-otp/'
        data = {
            'email': 'test@example.com',
            'otp_code': otp.otp_code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_verify_invalid_otp(self):
        """Test verification with invalid OTP"""
        url = '/auth/api/mobile/verify-otp/'
        data = {
            'email': 'test@example.com',
            'otp_code': '000000'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid OTP', response.data['error'])

    def test_resend_otp(self):
        """Test OTP resend functionality"""
        url = '/auth/api/mobile/resend-otp/'
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resent successfully', response.data['message'])

    def test_logout(self):
        """Test logout functionality"""
        # Create token for user
        token = Token.objects.create(user=self.user)
        
        url = '/auth/api/mobile/logout/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Logout successful', response.data['message'])
        
        # Check token was deleted
        self.assertFalse(Token.objects.filter(user=self.user).exists())


class OTPModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

    def test_otp_generation(self):
        """Test OTP generation"""
        otp = OTP.generate_otp(self.user, 'email', 'test@example.com')
        
        self.assertEqual(otp.user, self.user)
        self.assertEqual(otp.otp_type, 'email')
        self.assertEqual(len(otp.otp_code), 6)
        self.assertFalse(otp.is_used)
        self.assertEqual(otp.attempts, 0)

    def test_otp_verification(self):
        """Test OTP verification"""
        otp = OTP.generate_otp(self.user, 'email', 'test@example.com')
        
        # Valid verification
        is_valid, message = OTP.verify_otp(self.user, otp.otp_code, 'email')
        self.assertTrue(is_valid)
        self.assertIn('successfully', message)
        
        # Check OTP is marked as used
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_otp_expiry(self):
        """Test OTP expiry functionality"""
        otp = OTP.generate_otp(self.user, 'email', 'test@example.com')
        
        # OTP should be valid initially
        self.assertTrue(otp.is_valid())
        
        # Simulate expiry by setting expires_at to past
        from django.utils import timezone
        from datetime import timedelta
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        
        # OTP should be expired now
        self.assertFalse(otp.is_valid())
        self.assertTrue(otp.is_expired())