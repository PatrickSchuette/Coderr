from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from offers_app.models import Offer


class IsBusinessUser(permissions.BasePermission):
    """Allow access only to authenticated users whose profile type is 'business'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return True if the requesting user has a business profile."""
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.type == 'business')


class IsOfferOwner(permissions.BasePermission):
    """Allow write access to an offer only to the user who created it."""

    def has_object_permission(self, request: Request, view: APIView, obj: Offer) -> bool:
        """Return True if the requester is the owner of the given offer."""
        return obj.user_id == request.user.id
