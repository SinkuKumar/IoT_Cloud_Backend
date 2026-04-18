from rest_framework.permissions import BasePermission


class IsProjectOwner(BasePermission):
    """
    View-level:  only authenticated users may proceed.
    Object-level: access is granted only when the device's parent project
                  is owned by the requesting user.
    """

    message = "You do not have permission to access this device."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # obj is a Device; traverse project → owner
        return obj.project.owner_id == request.user.pk
