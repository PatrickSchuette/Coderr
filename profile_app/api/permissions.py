from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from profile_app.models import Profile


class IsProfileOwner(permissions.BasePermission):
    """Allow write access only to the profile owner; read access to any authenticated user."""

    def has_object_permission(self, request: Request, view: APIView, obj: Profile) -> bool:
        """Return True if the request is safe or the requester owns the profile."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
