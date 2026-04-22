from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCoach(BasePermission):
    """Allow access only to users with the coach role."""
    message = "Only coaches can perform this action."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'coach'
        )


class IsCoachOrReadOnly(BasePermission):
    """Allow coaches to write; all authenticated users to read."""
    message = "Only coaches can modify this data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return (
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'coach'
        )


class IsOwnerOrReadOnly(BasePermission):
    """Allow object owner to edit; others can only read."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or getattr(obj, 'created_by', None) == request.user
