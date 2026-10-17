from rest_framework import permissions
from apps.accounts.models import User

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to Admin users or Django superusers.
    """
    message = 'You must be an administrator to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.ADMIN or request.user.is_superuser or request.user.is_staff)
        )


class IsAgentUserRole(permissions.BasePermission):
    """
    Allows access to Support Agents and Admins.
    """
    message = 'You must be a support agent or administrator to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.AGENT, User.Role.ADMIN] or request.user.is_superuser)
        )


class IsCustomerUserRole(permissions.BasePermission):
    """
    Allows access to Customers.
    """
    message = 'You must be registered as a customer to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.CUSTOMER
        )
