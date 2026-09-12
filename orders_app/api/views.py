from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from orders_app.api.permissions import IsAssignedBusinessUser, IsCustomerUser
from orders_app.api.serializers import (OrderCreateSerializer, OrderSerializer, OrderStatusUpdateSerializer)
from orders_app.models import Order


class OrderListCreateView(generics.ListCreateAPIView):
    """List the user's own orders, or place a new one. Maps to /api/orders/."""

    pagination_class = None

    def get_queryset(self) -> QuerySet[Order]:
        """Return only orders where the requesting user is customer or business partner."""
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Use the create serializer for POST, the read serializer otherwise."""
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Only customers may place new orders; any authenticated user may list their own."""
        if self.request.method == 'POST':
            permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission_class() for permission_class in permission_classes]


class OrderDetailView(mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """Update an order's status or delete it. Maps to /api/orders/{id}/."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Only staff may delete orders; only the assigned business user may update status."""
        if self.request.method == 'DELETE':
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAssignedBusinessUser]
        return [permission_class() for permission_class in permission_classes]

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """Handle PATCH by delegating to the partial update mixin."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """Handle DELETE by delegating to the destroy mixin."""
        return self.destroy(request, *args, **kwargs)


class OrderCountView(APIView):
    """Return the number of in-progress orders for a business user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, business_user_id: int) -> Response:
        """Count in-progress orders assigned to the given business user."""
        business_user = get_object_or_404(User, id=business_user_id, profile__type='business')
        count = Order.objects.filter(business_user=business_user, status=Order.Status.IN_PROGRESS).count()
        return Response({'order_count': count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """Return the number of completed orders for a business user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, business_user_id: int) -> Response:
        """Count completed orders assigned to the given business user."""
        business_user = get_object_or_404(User, id=business_user_id, profile__type='business')
        count = Order.objects.filter(business_user=business_user, status=Order.Status.COMPLETED).count()
        return Response({'completed_order_count': count}, status=status.HTTP_200_OK)
