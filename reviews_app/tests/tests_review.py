from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from profile_app.models import Profile
from reviews_app.models import Review


def create_user_with_profile(username: str, profile_type: str) -> tuple[User, Token]:
    """Create a user with a matching profile and auth token for test setup."""
    user = User.objects.create_user(username=username, password='testpass123')
    Profile.objects.create(user=user, type=profile_type)
    token = Token.objects.create(user=user)
    return user, token


class ReviewListCreateTests(APITestCase):
    """Tests for GET/POST /api/reviews/."""

    def setUp(self) -> None:
        """Create a business user and a customer to act as reviewer."""
        self.business_user, self.business_token = create_user_with_profile(
            'reviewbiz', 'business')
        self.customer_user, self.customer_token = create_user_with_profile(
            'reviewcust', 'customer')
        self.url = reverse('review-list')

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_list_requires_authentication(self) -> None:
        """Listing reviews without a token should be rejected with 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_plain_array(self) -> None:
        """The review list should be a plain array, not a paginated object."""
        self.authenticate(self.customer_token)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_list_filters_by_business_user_id(self) -> None:
        """Filtering by business_user_id should only return reviews for that user."""
        other_business, _ = create_user_with_profile('otherbiz', 'business')
        Review.objects.create(business_user=self.business_user,
                              reviewer=self.customer_user, rating=4)
        another_customer, _ = create_user_with_profile(
            'anothercust', 'customer')
        Review.objects.create(business_user=other_business,
                              reviewer=another_customer, rating=5)
        self.authenticate(self.customer_token)

        response = self.client.get(
            self.url, {'business_user_id': self.business_user.id})

        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['business_user'], self.business_user.id)

    def test_create_requires_authentication(self) -> None:
        """Creating a review without a token should be rejected with 401."""
        response = self.client.post(
            self.url, {'business_user': self.business_user.id, 'rating': 4}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_forbidden_for_business_user(self) -> None:
        """A business user should not be allowed to create reviews."""
        self.authenticate(self.business_token)

        response = self.client.post(
            self.url, {'business_user': self.business_user.id, 'rating': 4}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_success_for_customer(self) -> None:
        """A customer should be able to create a review for a business user."""
        self.authenticate(self.customer_token)
        payload = {'business_user': self.business_user.id,
                   'rating': 4, 'description': 'Great work!'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.customer_user.id)
        self.assertEqual(Review.objects.count(), 1)

    def test_create_fails_when_target_is_not_a_business_user(self) -> None:
        """Targeting a non-business user with a review should be rejected with 400."""
        self.authenticate(self.customer_token)
        payload = {'business_user': self.customer_user.id, 'rating': 4}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_on_duplicate_review(self) -> None:
        """A reviewer submitting a second review for the same business should get 400."""
        self.authenticate(self.customer_token)
        payload = {'business_user': self.business_user.id, 'rating': 4}
        self.client.post(self.url, payload, format='json')

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)


class ReviewDetailTests(APITestCase):
    """Tests for PATCH/DELETE /api/reviews/{id}/."""

    def setUp(self) -> None:
        """Create a review authored by a customer for a business user."""
        self.business_user, _ = create_user_with_profile(
            'detailbiz', 'business')
        self.reviewer, self.reviewer_token = create_user_with_profile(
            'detailreviewer', 'customer')
        self.other_user, self.other_token = create_user_with_profile(
            'otherreviewer', 'customer')

        self.review = Review.objects.create(
            business_user=self.business_user, reviewer=self.reviewer, rating=3, description='Okay service.',
        )
        self.url = reverse('review-detail', kwargs={'pk': self.review.id})

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_patch_requires_authentication(self) -> None:
        """Updating a review without a token should be rejected with 401."""
        response = self.client.patch(self.url, {'rating': 5}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_update_rating_and_description(self) -> None:
        """The review's author should be able to update rating and description."""
        self.authenticate(self.reviewer_token)

        response = self.client.patch(
            self.url, {'rating': 5, 'description': 'Even better!'}, format='json')
        self.review.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.description, 'Even better!')

    def test_business_user_field_cannot_be_changed_via_patch(self) -> None:
        """The business_user field must stay read-only, even if included in the payload."""
        other_business, _ = create_user_with_profile('sneakybiz', 'business')
        self.authenticate(self.reviewer_token)

        self.client.patch(
            self.url, {'business_user': other_business.id}, format='json')
        self.review.refresh_from_db()

        self.assertEqual(self.review.business_user, self.business_user)

    def test_non_owner_cannot_update_review(self) -> None:
        """A user who did not author the review should receive 403 on PATCH."""
        self.authenticate(self.other_token)

        response = self.client.patch(self.url, {'rating': 1}, format='json')
        self.review.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.review.rating, 3)

    def test_owner_can_delete_review(self) -> None:
        """The review's author should be able to delete it."""
        self.authenticate(self.reviewer_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_non_owner_cannot_delete_review(self) -> None:
        """A user who did not author the review should receive 403 on DELETE."""
        self.authenticate(self.other_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())
