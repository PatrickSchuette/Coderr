from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer
from profile_app.models import Profile
from reviews_app.models import Review


def create_user_with_profile(username: str, profile_type: str) -> User:
    """Create a user with a matching profile for test setup."""
    user = User.objects.create_user(username=username, password='testpass123')
    Profile.objects.create(user=user, type=profile_type)
    return user


class BaseInfoTests(APITestCase):
    """Tests for GET /api/base-info/."""

    def setUp(self) -> None:
        """Define the URL used by every test in this class."""
        self.url = reverse('base-info')

    def test_base_info_does_not_require_authentication(self) -> None:
        """The endpoint should be publicly accessible."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_base_info_returns_zero_values_when_no_data_exists(self) -> None:
        """With an empty database, all counts should be 0 and the rating should not crash."""
        response = self.client.get(self.url)

        self.assertEqual(response.data['review_count'], 0)
        self.assertEqual(response.data['average_rating'], 0)
        self.assertEqual(response.data['business_profile_count'], 0)
        self.assertEqual(response.data['offer_count'], 0)

    def test_base_info_counts_reviews_and_computes_average_rating(self) -> None:
        """The review count and average rating should reflect all stored reviews."""
        business = create_user_with_profile('infobiz', 'business')
        reviewer_one = create_user_with_profile('reviewer1', 'customer')
        reviewer_two = create_user_with_profile('reviewer2', 'customer')
        Review.objects.create(business_user=business, reviewer=reviewer_one, rating=4)
        Review.objects.create(business_user=business, reviewer=reviewer_two, rating=5)

        response = self.client.get(self.url)

        self.assertEqual(response.data['review_count'], 2)
        self.assertEqual(response.data['average_rating'], 4.5)

    def test_base_info_counts_only_business_profiles(self) -> None:
        """Customer profiles should not be included in business_profile_count."""
        create_user_with_profile('infobiz2', 'business')
        create_user_with_profile('infocust', 'customer')

        response = self.client.get(self.url)

        self.assertEqual(response.data['business_profile_count'], 1)

    def test_base_info_counts_offers(self) -> None:
        """The offer count should reflect all stored offers."""
        business = create_user_with_profile('infobiz3', 'business')
        Offer.objects.create(user=business, title='Offer A')
        Offer.objects.create(user=business, title='Offer B')

        response = self.client.get(self.url)

        self.assertEqual(response.data['offer_count'], 2)
