from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, permissions
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from reviews_app.api.filters import ReviewFilter
from reviews_app.api.permissions import IsCustomerUser, IsReviewOwner
from reviews_app.api.serializers import (ReviewCreateSerializer, ReviewSerializer, ReviewUpdateSerializer)
from reviews_app.models import Review


class ReviewListCreateView(generics.ListCreateAPIView):
    """List all reviews, or create a new one. Maps to /api/reviews/."""

    queryset = Review.objects.all()
    pagination_class = None
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ['updated_at', 'rating']

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Use the create serializer for POST, the read serializer otherwise."""
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Only customers may create reviews; any authenticated user may list them."""
        if self.request.method == 'POST':
            permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission_class() for permission_class in permission_classes]


class ReviewDetailView(mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    """Update or delete a review. Maps to /api/reviews/{id}/. Owner-only."""

    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewOwner]

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """Handle PATCH by delegating to the partial update mixin."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """Handle DELETE by delegating to the destroy mixin."""
        return self.destroy(request, *args, **kwargs)
