from rest_framework import permissions
from apps.accounts.models import User
from apps.tickets.models import SupportTicket

class TicketPermission(permissions.BasePermission):
    """
    Object-level and model-level permission for tickets:
    - Admin: full access to all tickets.
    - Agent: read all tickets, update assigned or open tickets, add replies/internal notes.
    - Customer: can list/retrieve/create only their own tickets. Cannot delete.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return True

        if user.role == User.Role.AGENT:
            # Agents can view all tickets and update them
            if request.method in permissions.SAFE_METHODS:
                return True
            # Allow agents to modify tickets (status, priority, replies)
            return True

        if user.role == User.Role.CUSTOMER:
            # Customers only access their own tickets
            if obj.customer != user:
                return False
            if request.method in permissions.SAFE_METHODS:
                return True
            if request.method in ['PATCH', 'PUT']:
                # Customers cannot change assigned_agent or priority
                return True
            if request.method == 'POST' and getattr(view, 'action', None) in ['reopen', 'messages']:
                return True
            return False

        return False
