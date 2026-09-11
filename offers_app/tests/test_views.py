from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from profile_app.models import Profile


def create_user_with_profile(username: str, profile_type: str) -> tuple[User, Token]:
    """Create a user with a matching profile and auth token for test setup."""
    user = User.objects.create_user(username=username, password='testpass123')
    Profile.objects.create(user=user, type=profile_type)
    token = Token.objects.create(user=user)
    return user, token


def build_offer_payload() -> dict:
    """Return a valid offer creation payload with all three required tiers."""
    return {
        'title': 'Grafikdesign-Paket',
        'description': 'Ein umfassendes Grafikdesign-Paket.',
        'details': [
            {'title': 'Basic', 'revisions': 2, 'delivery_time_in_days': 5,'price': 100, 'features': ['Logo'], 'offer_type': 'basic'},
            {'title': 'Standard', 'revisions': 5, 'delivery_time_in_days': 7,'price': 200, 'features': ['Logo', 'Flyer'], 'offer_type': 'standard'},
            {'title': 'Premium', 'revisions': 10, 'delivery_time_in_days': 10,'price': 500, 'features': ['Logo', 'Flyer', 'Card'], 'offer_type': 'premium'},
        ],
    }


class OfferListTests(APITestCase):
    """Tests for GET /api/offers/."""

    def setUp(self) -> None:
        """Create a business user with one offer containing three price tiers."""
        self.business_user, self.business_token = create_user_with_profile('bizuser', 'business')
        self.offer = Offer.objects.create(user=self.business_user, title='Website Design')
        OfferDetail.objects.create(offer=self.offer, title='Basic', revisions=2, delivery_time_in_days=7,price=100, features=['Logo'], offer_type='basic')
        OfferDetail.objects.create(offer=self.offer, title='Standard', revisions=5, delivery_time_in_days=5,price=200, features=['Logo', 'Flyer'], offer_type='standard')
        OfferDetail.objects.create(offer=self.offer, title='Premium', revisions=10, delivery_time_in_days=3,price=500, features=['Logo', 'Flyer', 'Card'], offer_type='premium')
        self.url = reverse('offer-list')

    def test_list_offers_does_not_require_authentication(self) -> None:
        """The offer list should be publicly accessible."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_offers_includes_min_price_and_min_delivery_time(self) -> None:
        """The list should report the cheapest price and shortest delivery time."""
        response = self.client.get(self.url)
        result = response.data['results'][0]

        self.assertEqual(float(result['min_price']), 100.0)
        self.assertEqual(result['min_delivery_time'], 3)

    def test_list_offers_filters_by_creator_id(self) -> None:
        """Filtering by creator_id should only return that user's offers."""
        other_user, _ = create_user_with_profile('otherbiz', 'business')
        Offer.objects.create(user=other_user, title='Other Offer')

        response = self.client.get(self.url, {'creator_id': self.business_user.id})

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.business_user.id)

    def test_list_offers_filters_by_max_delivery_time(self) -> None:
        """Offers whose fastest tier exceeds max_delivery_time should be excluded."""
        response_matching = self.client.get(self.url, {'max_delivery_time': 3})
        response_excluding = self.client.get(self.url, {'max_delivery_time': 1})

        self.assertEqual(response_matching.data['count'], 1)
        self.assertEqual(response_excluding.data['count'], 0)

    def test_list_offers_search_matches_title(self) -> None:
        """The search parameter should match against the offer title."""
        response = self.client.get(self.url, {'search': 'Website'})

        self.assertEqual(response.data['count'], 1)

    def test_list_offers_respects_page_size_parameter(self) -> None:
        """The page_size query parameter should override the default page size."""
        for index in range(5):
            Offer.objects.create(user=self.business_user,title=f'Offer {index}')

        response = self.client.get(self.url, {'page_size': 2})

        self.assertEqual(len(response.data['results']), 2)


class OfferCreateTests(APITestCase):
    """Tests for POST /api/offers/."""

    def setUp(self) -> None:
        """Create a business and a customer user for permission checks."""
        self.business_user, self.business_token = create_user_with_profile('bizcreator', 'business')
        self.customer_user, self.customer_token = create_user_with_profile('customercreator', 'customer')
        self.url = reverse('offer-list')

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_create_offer_requires_authentication(self) -> None:
        """An unauthenticated request should be rejected with 401."""
        response = self.client.post(self.url, build_offer_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_offer_forbidden_for_customer(self) -> None:
        """A customer user should not be allowed to create offers."""
        self.authenticate(self.customer_token)

        response = self.client.post(self.url, build_offer_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_success_for_business_user(self) -> None:
        """A business user should be able to create an offer with three tiers."""
        self.authenticate(self.business_token)

        response = self.client.post(self.url, build_offer_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['details']), 3)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(Offer.objects.first().user, self.business_user)

    def test_create_offer_fails_with_fewer_than_three_details(self) -> None:
        """An offer with fewer than 3 details should be rejected with 400."""
        self.authenticate(self.business_token)
        payload = build_offer_payload()
        payload['details'] = payload['details'][:2]

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_fails_with_duplicate_offer_type(self) -> None:
        """An offer with two tiers of the same type should be rejected with 400."""
        self.authenticate(self.business_token)
        payload = build_offer_payload()
        payload['details'][1]['offer_type'] = 'basic'

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferRetrieveUpdateDeleteTests(APITestCase):
    """Tests for GET/PATCH/DELETE /api/offers/{id}/."""

    def setUp(self) -> None:
        """Create an offer owned by a business user, plus an unrelated second user."""
        self.owner, self.owner_token = create_user_with_profile('offerowner', 'business')
        self.other_user, self.other_token = create_user_with_profile('otheruser', 'business')

        self.offer = Offer.objects.create(user=self.owner, title='Website Design')
        OfferDetail.objects.create(offer=self.offer, title='Basic', revisions=2, delivery_time_in_days=5,price=100, features=['Logo'], offer_type='basic')
        self.url = reverse('offer-detail', kwargs={'pk': self.offer.id})

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_retrieve_offer_requires_authentication(self) -> None:
        """Fetching a single offer without a token should be rejected with 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_offer_success(self) -> None:
        """An authenticated user should be able to retrieve any single offer."""
        self.authenticate(self.other_token)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.offer.id)

    def test_retrieve_nonexistent_offer_returns_404(self) -> None:
        """Requesting a non-existent offer ID should return 404."""
        self.authenticate(self.owner_token)
        url = reverse('offer-detail', kwargs={'pk': 9999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_offer(self) -> None:
        """The offer owner should be able to update the offer's own fields."""
        self.authenticate(self.owner_token)

        response = self.client.patch(self.url, {'title': 'Updated Title'}, format='json')
        self.offer.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.offer.title, 'Updated Title')

    def test_owner_can_update_a_single_detail_tier_by_offer_type(self) -> None:
        """Updating one tier via offer_type should leave the offer's other data intact."""
        self.authenticate(self.owner_token)
        payload = {'details': [{'offer_type': 'basic', 'title': 'Basic Updated', 'revisions': 3, 'delivery_time_in_days': 4, 'price': 120, 'features': ['Logo', 'Flyer']}]}

        response = self.client.patch(self.url, payload, format='json')
        detail = self.offer.details.get(offer_type='basic')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.title, 'Basic Updated')
        self.assertEqual(float(detail.price), 120.0)

    def test_non_owner_cannot_update_offer(self) -> None:
        """A user who does not own the offer should receive 403 on PATCH."""
        self.authenticate(self.other_token)

        response = self.client.patch(
            self.url, {'title': 'Hacked Title'}, format='json')
        self.offer.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(self.offer.title, 'Hacked Title')

    def test_owner_can_delete_offer(self) -> None:
        """The offer owner should be able to delete the offer."""
        self.authenticate(self.owner_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=self.offer.id).exists())

    def test_non_owner_cannot_delete_offer(self) -> None:
        """A user who does not own the offer should receive 403 on DELETE."""
        self.authenticate(self.other_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=self.offer.id).exists())


class OfferDetailRetrieveViewTests(APITestCase):
    """Tests for GET /api/offerdetails/{id}/."""

    def setUp(self) -> None:
        """Create an offer with one detail tier and an authenticated user."""
        owner, _ = create_user_with_profile('detailowner', 'business')
        self.user, self.token = create_user_with_profile('detailreader', 'customer')
        offer = Offer.objects.create(user=owner, title='Website Design')
        self.detail = OfferDetail.objects.create(offer=offer, title='Basic', revisions=2, delivery_time_in_days=5,price=100, features=['Logo'], offer_type='basic')
        self.url = reverse('offerdetail-detail', kwargs={'pk': self.detail.id})

    def test_retrieve_offerdetail_requires_authentication(self) -> None:
        """Fetching an offer detail without a token should be rejected with 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_offerdetail_success(self) -> None:
        """An authenticated user should be able to retrieve a single offer detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Basic')
        self.assertEqual(response.data['offer_type'], 'basic')
