from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from orders_app.models import Order
from profile_app.models import Profile


def create_user_with_profile(username: str, profile_type: str) -> tuple[User, Token]:
    """Create a user with a matching profile and auth token for test setup."""
    user = User.objects.create_user(username=username, password='testpass123')
    Profile.objects.create(user=user, type=profile_type)
    token = Token.objects.create(user=user)
    return user, token


def create_offer_detail(owner: User, offer_type: str = 'basic', price: int = 100) -> OfferDetail:
    """Create a minimal offer with a single detail tier, owned by the given business user."""
    offer = Offer.objects.create(user=owner, title='Website Design')
    return OfferDetail.objects.create(offer=offer, title='Basic', revisions=2, delivery_time_in_days=5, price=price, features=['Logo'], offer_type=offer_type)


class OrderListCreateTests(APITestCase):
    """Tests for GET/POST /api/orders/."""

    def setUp(self) -> None:
        """Create a business user with an offer detail and a customer to order it."""
        self.business_user, self.business_token = create_user_with_profile('orderbiz', 'business')
        self.customer_user, self.customer_token = create_user_with_profile('ordercust', 'customer')
        self.offer_detail = create_offer_detail(self.business_user)
        self.url = reverse('order-list')

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_list_orders_requires_authentication(self) -> None:
        """Listing orders without a token should be rejected with 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_plain_array_not_paginated(self) -> None:
        """The order list should be a plain array, not a paginated object."""
        self.authenticate(self.customer_token)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_list_only_includes_orders_involving_the_requester(self) -> None:
        """Unrelated users should not see orders they are not part of."""
        Order.objects.create(customer_user=self.customer_user, business_user=self.business_user,title='X', revisions=1, delivery_time_in_days=1, price=10, offer_type='basic')
        unrelated_user, unrelated_token = create_user_with_profile('unrelated', 'customer')

        response = self.client.get(self.url, **{'HTTP_AUTHORIZATION': f'Token {unrelated_token.key}'})

        self.assertEqual(response.data, [])

    def test_create_order_requires_authentication(self) -> None:
        """Placing an order without a token should be rejected with 401."""
        response = self.client.post(self.url, {'offer_detail_id': self.offer_detail.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_forbidden_for_business_user(self) -> None:
        """A business user should not be allowed to place an order."""
        self.authenticate(self.business_token)

        response = self.client.post(self.url, {'offer_detail_id': self.offer_detail.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_success_for_customer(self) -> None:
        """A customer should be able to place an order, snapshotting the offer detail."""
        self.authenticate(self.customer_token)

        response = self.client.post(self.url, {'offer_detail_id': self.offer_detail.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_user'], self.customer_user.id)
        self.assertEqual(response.data['business_user'], self.business_user.id)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(float(response.data['price']), 100.0)

    def test_create_order_with_nonexistent_offer_detail_returns_404(self) -> None:
        """Referencing a non-existent offer_detail_id should return 404."""
        self.authenticate(self.customer_token)

        response = self.client.post(self.url, {'offer_detail_id': 9999}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderDetailTests(APITestCase):
    """Tests for PATCH/DELETE /api/orders/{id}/."""

    def setUp(self) -> None:
        """Create an order between a business and a customer user."""
        self.business_user, self.business_token = create_user_with_profile('detailbiz', 'business')
        self.other_business_user, self.other_business_token = create_user_with_profile('otherbiz', 'business')
        self.customer_user, self.customer_token = create_user_with_profile('detailcust', 'customer')
        self.admin_user = User.objects.create_superuser(username='admin', password='testpass123')
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.order = Order.objects.create(customer_user=self.customer_user, business_user=self.business_user,title='Logo Design', revisions=3, delivery_time_in_days=5, price=150, features=['Logo'], offer_type='basic')
        self.url = reverse('order-detail', kwargs={'pk': self.order.id})

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_patch_status_requires_authentication(self) -> None:
        """Updating status without a token should be rejected with 401."""
        response = self.client.patch(self.url, {'status': 'completed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assigned_business_user_can_update_status(self) -> None:
        """The business user assigned to the order should be able to change its status."""
        self.authenticate(self.business_token)

        response = self.client.patch(self.url, {'status': 'completed'}, format='json')
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.status, 'completed')

    def test_other_business_user_cannot_update_status(self) -> None:
        """A business user not assigned to the order should receive 403."""
        self.authenticate(self.other_business_token)

        response = self.client.patch(self.url, {'status': 'completed'}, format='json')
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.order.status, 'in_progress')

    def test_customer_cannot_update_status(self) -> None:
        """The customer who placed the order should not be able to change its status."""
        self.authenticate(self.customer_token)

        response = self.client.patch(self.url, {'status': 'completed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_delete_order(self) -> None:
        """A regular authenticated user should not be able to delete an order."""
        self.authenticate(self.business_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=self.order.id).exists())

    def test_admin_can_delete_order(self) -> None:
        """A staff user should be able to delete any order."""
        self.authenticate(self.admin_token)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())


class OrderCountTests(APITestCase):
    """Tests for GET /api/order-count/{id}/ and /api/completed-order-count/{id}/."""

    def setUp(self) -> None:
        """Create a business user with one in-progress and one completed order."""
        self.business_user, self.business_token = create_user_with_profile('countbiz', 'business')
        self.customer_user, self.customer_token = create_user_with_profile('countcust', 'customer')

        Order.objects.create(customer_user=self.customer_user, business_user=self.business_user, title='A', revisions=1, delivery_time_in_days=1, price=10, offer_type='basic', status='in_progress')
        Order.objects.create(customer_user=self.customer_user, business_user=self.business_user, title='B', revisions=1, delivery_time_in_days=1, price=10, offer_type='basic', status='in_progress')
        Order.objects.create(customer_user=self.customer_user, business_user=self.business_user, title='C', revisions=1, delivery_time_in_days=1, price=10, offer_type='basic', status='completed')

    def authenticate(self, token: Token) -> None:
        """Attach the given token as the Authorization header for this client."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_order_count_requires_authentication(self) -> None:
        """Requesting the order count without a token should be rejected with 401."""
        url = reverse('order-count', kwargs={'business_user_id': self.business_user.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_count_returns_in_progress_count(self) -> None:
        """The in-progress order count should only include orders with that status."""
        self.authenticate(self.customer_token)
        url = reverse('order-count', kwargs={'business_user_id': self.business_user.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 2)

    def test_completed_order_count_returns_correct_count(self) -> None:
        """The completed order count should only include orders with that status."""
        self.authenticate(self.customer_token)
        url = reverse('completed-order-count', kwargs={'business_user_id': self.business_user.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completed_order_count'], 1)

    def test_order_count_for_nonexistent_business_user_returns_404(self) -> None:
        """Requesting counts for a non-existent user ID should return 404."""
        self.authenticate(self.customer_token)
        url = reverse('order-count', kwargs={'business_user_id': 9999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_count_for_customer_id_returns_404(self) -> None:
        """A user ID belonging to a customer (not a business) should return 404."""
        self.authenticate(self.business_token)
        url = reverse('order-count', kwargs={'business_user_id': self.customer_user.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
