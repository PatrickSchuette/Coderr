from django.db.models import Min, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import BaseSerializer

from offers_app.api.filters import OfferFilter
from offers_app.api.permissions import IsBusinessUser, IsOfferOwner
from offers_app.api.serializers import (OfferCreateSerializer,OfferDetailWriteSerializer,OfferListSerializer,OfferRetrieveSerializer,OfferUpdateSerializer,)
from offers_app.models import Offer, OfferDetail


class OfferPagination(PageNumberPagination):
    """Default page size of 6, overridable via the 'page_size' query parameter."""

    page_size = 6
    page_size_query_param = 'page_size'


class OfferViewSet(viewsets.ModelViewSet):
    """CRUD endpoint for offers. Maps to /api/offers/ and /api/offers/{id}/."""

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']
    pagination_class = OfferPagination

    def get_queryset(self) -> QuerySet[Offer]:
        """Annotate each offer with its cheapest price and shortest delivery time."""
        return (
            Offer.objects.select_related('user__profile')
            .prefetch_related('details')
            .annotate(min_price=Min('details__price'), min_delivery_time=Min('details__delivery_time_in_days'))
            .order_by('-created_at')
        )

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Pick the serializer that matches the current action's expected shape."""
        if self.action == 'list':
            return OfferListSerializer
        if self.action == 'create':
            return OfferCreateSerializer
        if self.action in ('update', 'partial_update'):
            return OfferUpdateSerializer
        return OfferRetrieveSerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Apply the documented, action-specific permission rules."""
        if self.action == 'list':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsBusinessUser]
        elif self.action in ('update', 'partial_update', 'destroy'):
            permission_classes = [permissions.IsAuthenticated, IsOfferOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission_class() for permission_class in permission_classes]


class OfferDetailRetrieveView(generics.RetrieveAPIView):
    """Retrieve a single pricing tier. GET /api/offerdetails/{id}/."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
