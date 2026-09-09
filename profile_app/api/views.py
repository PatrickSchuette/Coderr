from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from profile_app.api.permissions import IsProfileOwner
from profile_app.api.serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileDetailSerializer,
)
from profile_app.models import Profile


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a single profile.

    GET   /api/profile/{pk}/ - retrieve profile details (pk = user ID).
    PATCH /api/profile/{pk}/ - update the authenticated user's own profile.
    """

    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated, IsProfileOwner]
    lookup_field = 'user_id'
    lookup_url_kwarg = 'pk'


class BusinessProfileListView(generics.ListAPIView):
    """List all business profiles. GET /api/profiles/business/."""

    queryset = Profile.objects.select_related('user').filter(type=Profile.ProfileType.BUSINESS)
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class CustomerProfileListView(generics.ListAPIView):
    """List all customer profiles. GET /api/profiles/customer/."""

    queryset = Profile.objects.select_related('user').filter(type=Profile.ProfileType.CUSTOMER)
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
