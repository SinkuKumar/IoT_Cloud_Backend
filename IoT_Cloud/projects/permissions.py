from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS


class IsOwner(BasePermission):
    """
    Object-level permission: allow access only to the owner of the project.
    Assumes the model instance has an `owner` attribute.
    """

    message = "You do not have permission to access this project."

    def has_permission(self, request, view):
        # Require authentication for every action
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.pk
