from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class LogoutTests(APITestCase):
    """Tests for POST /api/logout/."""

    def setUp(self) -> None:
        """Create a user with a token and define the logout URL."""
        self.user = User.objects.create_user(username='logoutuser', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.url = reverse('logout')

    def test_logout_requires_authentication(self) -> None:
        """Logging out without a token should be rejected with 401."""
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_the_token(self) -> None:
        """A successful logout should remove the token from the database."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_token_no_longer_works_after_logout(self) -> None:
        """A request made with the deleted token should be rejected with 401."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.client.post(self.url)

        response = self.client.get(reverse('profile-detail', kwargs={'pk': self.user.id}))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
