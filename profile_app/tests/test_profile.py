from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from profile_app.models import Profile


class ProfileDetailTests(APITestCase):
    """Tests for GET/PATCH /api/profile/{pk}/."""

    def setUp(self) -> None:
        """Create an owner user with a profile and a second, unrelated user."""
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.owner_profile = Profile.objects.create(user=self.owner, type='business')
        self.owner_token = Token.objects.create(user=self.owner)

        self.other_user = User.objects.create_user(username='other', password='testpass123')
        Profile.objects.create(user=self.other_user, type='customer')
        self.other_token = Token.objects.create(user=self.other_user)

        self.url = reverse('profile-detail', kwargs={'pk': self.owner.id})

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_retrieve_profile_requires_authentication(self) -> None:
        """A request without a token should be rejected with 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_profile_succeeds(self) -> None:
        """An authenticated user should be able to retrieve their own profile."""
        self.authenticate(self.owner_token)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.owner.id)
        self.assertEqual(response.data['type'], 'business')

    def test_blank_fields_are_returned_as_empty_string_not_null(self) -> None:
        """Untouched text fields must serialize as '' instead of null."""
        self.authenticate(self.owner_token)

        response = self.client.get(self.url)

        for field in ('first_name', 'last_name', 'location', 'tel', 'description', 'working_hours'):
            self.assertEqual(response.data[field], '')

    def test_retrieve_other_users_profile_is_allowed_for_authenticated_users(self) -> None:
        """Reading a profile is not restricted to its owner, only writing is."""
        self.authenticate(self.other_token)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_nonexistent_profile_returns_404(self) -> None:
        """Requesting a profile for a non-existent user ID should return 404."""
        self.authenticate(self.owner_token)
        url = reverse('profile-detail', kwargs={'pk': 9999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_own_profile(self) -> None:
        """The owner should be able to update their own profile fields."""
        self.authenticate(self.owner_token)
        payload = {
            'first_name': 'Max',
            'last_name': 'Mustermann',
            'location': 'Berlin',
            'tel': '123456789',
            'description': 'Updated description',
            'working_hours': '9-17',
        }

        response = self.client.patch(self.url, payload, format='json')
        self.owner_profile.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.owner_profile.first_name, 'Max')
        self.assertEqual(self.owner_profile.location, 'Berlin')

    def test_owner_can_update_email_on_related_user(self) -> None:
        """Updating the email field should update the related User object."""
        self.authenticate(self.owner_token)

        response = self.client.patch(
            self.url, {'email': 'new@business.de'}, format='json')
        self.owner.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.owner.email, 'new@business.de')

    def test_non_owner_cannot_update_profile(self) -> None:
        """A user who is not the profile owner should receive 403 on PATCH."""
        self.authenticate(self.other_token)

        response = self.client.patch(
            self.url, {'first_name': 'Hacker'}, format='json')
        self.owner_profile.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(self.owner_profile.first_name, 'Hacker')

    def test_type_field_cannot_be_changed_via_patch(self) -> None:
        """The profile type must stay read-only, even if included in the payload."""
        self.authenticate(self.owner_token)

        self.client.patch(self.url, {'type': 'customer'}, format='json')
        self.owner_profile.refresh_from_db()

        self.assertEqual(self.owner_profile.type, 'business')
