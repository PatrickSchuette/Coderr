from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from orders_app.models import Order


class IsCustomerUser(permissions.BasePermission):
    """Allow access only to authenticated users whose profile type is 'customer'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return True if the requesting user has a customer profile."""
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.type == 'customer')


class IsAssignedBusinessUser(permissions.BasePermission):
    """Allow status updates only to the business user the order is assigned to."""

    def has_object_permission(self, request: Request, view: APIView, obj: Order) -> bool:
        """Return True if the requester is the order's assigned business user."""
        return obj.business_user_id == request.user.id
