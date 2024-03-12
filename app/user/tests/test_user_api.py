"""
Tests for the user API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Tests the public features of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test that creating a new user is successful"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload.get('email'))
        self.assertTrue(user.check_password(payload.get('password')))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exist_error(self):
        """Tests that error is returned when a user with email address exists
        """
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Tests that an error is returned if password < 5 characters"""
        payload = {
            'email': 'test@example.com',
            'password': 'tes',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload.get('email')
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates tokens for valid credentials."""
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**user_details)
        payload = {
            'email': user_details.get('email'),
            'password': user_details.get('password'),
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error is credentials invalid."""
        create_user(email='test@example.com', password='goodpass')
        payload = {
            'email': 'test@example.com',
            'password': 'badpass',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test passing blank password returns an error."""
        create_user(email='test@example.com', password='goodpass')
        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test user',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Tests retrieving profile for authenticated users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST method is not allowed for the me/ endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Tests updating the profile for authenticated user"""
        payload = {
            'name': 'Updated name',
            'password': 'newpassword123',
        }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload.get('name'))
        self.assertTrue(self.user.check_password(payload.get('password')))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
