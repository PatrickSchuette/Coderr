from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class LoginTests(APITestCase):
    """Tests for POST /api/login/."""

    def setUp(self) -> None:
        """Create a user to log in with and define the login URL."""
        self.url = reverse('login')
        self.user = User.objects.create_user(
            username='existinguser',
            email='existinguser@test.de',
            password='correctpass123',
        )

    def test_login_success_returns_200_with_token(self) -> None:
        """Correct credentials should return 200 with token and user data."""
        payload = {'username': 'existinguser', 'password': 'correctpass123'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'existinguser')
        self.assertEqual(response.data['email'], 'existinguser@test.de')
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_returns_existing_token_if_already_created(self) -> None:
        """A user who already has a token should get the same token again, not a new one."""
        existing_token = Token.objects.create(user=self.user)
        payload = {'username': 'existinguser', 'password': 'correctpass123'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.data['token'], existing_token.key)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_login_fails_with_wrong_password(self) -> None:
        """An incorrect password should be rejected with 400."""
        payload = {'username': 'existinguser', 'password': 'wrongpass'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_fails_with_unknown_username(self) -> None:
        """A username that does not exist should be rejected with 400."""
        payload = {'username': 'ghostuser', 'password': 'whatever123'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_fails_with_missing_password(self) -> None:
        """A request without a password should be rejected with 400, not 500."""
        payload = {'username': 'existinguser'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
