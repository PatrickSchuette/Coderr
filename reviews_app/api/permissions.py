from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from reviews_app.models import Review


class IsCustomerUser(permissions.BasePermission):
    """Allow access only to authenticated users whose profile type is 'customer'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return True if the requesting user has a customer profile."""
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.type == 'customer')


class IsReviewOwner(permissions.BasePermission):
    """Allow write access to a review only to the user who created it."""

    def has_object_permission(self, request: Request, view: APIView, obj: Review) -> bool:
        """Return True if the requester is the author of the given review."""
        return obj.reviewer_id == request.user.id
