from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from profile_app.models import Profile


class RegistrationTests(APITestCase):
    """Tests for POST /api/registration/."""

    def setUp(self) -> None:
        """Define the URL used by every test in this class."""
        self.url = reverse('registration')

    def test_registration_success_returns_201_with_token(self) -> None:
        """A valid payload should create a user and return token/user data."""
        payload = {
            'username': 'newbusiness',
            'email': 'newbusiness@test.de',
            'password': 'testpass123',
            'repeated_password': 'testpass123',
            'type': 'business',
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'newbusiness')
        self.assertEqual(response.data['email'], 'newbusiness@test.de')
        self.assertTrue(User.objects.filter(username='newbusiness').exists())

    def test_registration_creates_matching_profile(self) -> None:
        """The user's profile should be created automatically with the given type."""
        payload = {
            'username': 'newcustomer',
            'email': 'newcustomer@test.de',
            'password': 'testpass123',
            'repeated_password': 'testpass123',
            'type': 'customer',
        }

        response = self.client.post(self.url, payload, format='json')
        user = User.objects.get(username='newcustomer')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Profile.objects.filter(
            user=user, type='customer').exists())

    def test_registration_returns_working_token(self) -> None:
        """The returned token should match the token stored in the database."""
        payload = {
            'username': 'tokenuser',
            'email': 'tokenuser@test.de',
            'password': 'testpass123',
            'repeated_password': 'testpass123',
            'type': 'business',
        }

        response = self.client.post(self.url, payload, format='json')
        user = User.objects.get(username='tokenuser')
        stored_token = Token.objects.get(user=user)

        self.assertEqual(response.data['token'], stored_token.key)

    def test_registration_fails_on_password_mismatch(self) -> None:
        """Mismatched passwords should be rejected with 400."""
        payload = {
            'username': 'mismatchuser',
            'email': 'mismatch@test.de',
            'password': 'testpass123',
            'repeated_password': 'differentpass',
            'type': 'business',
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_registration_fails_on_duplicate_username(self) -> None:
        """Registering with an already-taken username should be rejected with 400."""
        User.objects.create_user(username='taken', password='testpass123')
        payload = {
            'username': 'taken',
            'email': 'other@test.de',
            'password': 'testpass123',
            'repeated_password': 'testpass123',
            'type': 'business',
        }

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_fails_on_missing_fields(self) -> None:
        """A payload missing required fields should be rejected with 400."""
        payload = {'username': 'incomplete'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
