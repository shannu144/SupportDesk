from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import User
from apps.accounts.permissions import IsAdminUserRole, IsAgentUserRole
from apps.tickets.models import (
    TicketCategory,
    SupportTicket,
    TicketMessage,
    TicketActivity,
)
from apps.tickets.serializers import (
    TicketCategorySerializer,
    SupportTicketListSerializer,
    SupportTicketDetailSerializer,
    SupportTicketCreateSerializer,
    TicketAssignSerializer,
    TicketMessageSerializer,
    TicketActivitySerializer,
)
from apps.tickets.permissions import TicketPermission


class TicketCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for ticket categories.
    List/Retrieve: All authenticated users.
    Create/Update/Delete: Admins only.
    """
    queryset = TicketCategory.objects.annotate(ticket_count=Count('tickets')).order_by('name')
    serializer_class = TicketCategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserRole()]
        return [permissions.IsAuthenticated()]


class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD, search, filter, sorting, assignment, and messaging for tickets.
    """
    permission_classes = [permissions.IsAuthenticated, TicketPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_agent']
    search_fields = ['ticket_number', 'subject', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SupportTicket.objects.none()

        user = self.request.user
        if not user or not user.is_authenticated:
            return SupportTicket.objects.none()

        queryset = SupportTicket.objects.select_related(
            'customer', 'assigned_agent', 'category'
        ).annotate(messages_count=Count('messages'))

        # Role-based scoping
        if user.role == User.Role.CUSTOMER:
            return queryset.filter(customer=user)
        # Agents and Admins see all tickets
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return SupportTicketDetailSerializer
        return SupportTicketListSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            ticket = serializer.save(customer=self.request.user)
            # Log initial activity
            TicketActivity.objects.create(
                ticket=ticket,
                actor=self.request.user,
                activity_type=TicketActivity.ActivityType.CREATED,
                details=f"Ticket {ticket.ticket_number} created with priority {ticket.priority}."
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_status = instance.status
        old_priority = instance.priority
        old_assignee = instance.assigned_agent

        with transaction.atomic():
            updated_ticket = serializer.save()

            # Record status change
            if old_status != updated_ticket.status:
                TicketActivity.objects.create(
                    ticket=updated_ticket,
                    actor=self.request.user,
                    activity_type=TicketActivity.ActivityType.STATUS_CHANGE,
                    old_value=old_status,
                    new_value=updated_ticket.status,
                    details=f"Status changed from {old_status} to {updated_ticket.status}."
                )

            # Record priority change
            if old_priority != updated_ticket.priority:
                TicketActivity.objects.create(
                    ticket=updated_ticket,
                    actor=self.request.user,
                    activity_type=TicketActivity.ActivityType.PRIORITY_CHANGE,
                    old_value=old_priority,
                    new_value=updated_ticket.priority,
                    details=f"Priority changed from {old_priority} to {updated_ticket.priority}."
                )

            # Record assignee change
            if old_assignee != updated_ticket.assigned_agent:
                old_name = old_assignee.get_full_name() if old_assignee else "Unassigned"
                new_name = updated_ticket.assigned_agent.get_full_name() if updated_ticket.assigned_agent else "Unassigned"
                TicketActivity.objects.create(
                    ticket=updated_ticket,
                    actor=self.request.user,
                    activity_type=TicketActivity.ActivityType.ASSIGNMENT_CHANGE,
                    old_value=old_name,
                    new_value=new_name,
                    details=f"Assignment changed from {old_name} to {new_name}."
                )

    def destroy(self, request, *args, **kwargs):
        # Admin-only delete
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
            return Response(
                {"detail": "Only administrators can delete tickets."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAgentUserRole])
    def assign(self, request, pk=None):
        """
        Assign or reassign ticket to a support agent.
        Admins and Agents only.
        """
        ticket = self.get_object()
        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agent_id = serializer.validated_data['assigned_agent_id']
        agent = None
        if agent_id:
            try:
                agent = User.objects.get(id=agent_id, role__in=[User.Role.AGENT, User.Role.ADMIN], is_active=True)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Support agent not found or inactive."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        old_assignee = ticket.assigned_agent
        with transaction.atomic():
            ticket.assigned_agent = agent
            # If ticket was open and is now assigned, optionally move to in_progress
            if agent and ticket.status == SupportTicket.Status.OPEN:
                ticket.status = SupportTicket.Status.IN_PROGRESS
            ticket.save()

            old_name = old_assignee.get_full_name() if old_assignee else "Unassigned"
            new_name = agent.get_full_name() if agent else "Unassigned"

            TicketActivity.objects.create(
                ticket=ticket,
                actor=request.user,
                activity_type=TicketActivity.ActivityType.ASSIGNMENT_CHANGE,
                old_value=old_name,
                new_value=new_name,
                details=f"Ticket assigned to {new_name} by {request.user.get_full_name()}."
            )

        return Response(SupportTicketDetailSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """
        Customer or staff can reopen an eligible resolved/closed ticket.
        """
        ticket = self.get_object()
        if ticket.status not in [SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]:
            return Response(
                {"detail": "Only resolved or closed tickets can be reopened."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            old_status = ticket.status
            ticket.status = SupportTicket.Status.OPEN
            ticket.resolved_at = None
            ticket.save()

            TicketActivity.objects.create(
                ticket=ticket,
                actor=request.user,
                activity_type=TicketActivity.ActivityType.REOPENED,
                old_value=old_status,
                new_value=SupportTicket.Status.OPEN,
                details=f"Ticket was reopened by {request.user.get_full_name()}."
            )

        return Response(SupportTicketDetailSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        GET /tickets/{id}/messages/ -> list messages (strips internal notes for customers)
        POST /tickets/{id}/messages/ -> add message or internal note
        """
        ticket = self.get_object()

        if request.method == 'GET':
            messages_qs = ticket.messages.select_related('author').order_by('created_at')
            # Security: enforce internal note invisibility for customer
            if not (request.user.is_staff or request.user.role in [User.Role.ADMIN, User.Role.AGENT] or request.user.is_superuser):
                messages_qs = messages_qs.filter(is_internal=False)
            serializer = TicketMessageSerializer(messages_qs, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            data = request.data.copy()
            is_internal = data.get('is_internal', False)

            # Customer cannot post internal notes
            if is_internal and request.user.role == User.Role.CUSTOMER:
                return Response(
                    {"detail": "Customers are not permitted to add internal notes."},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                message_obj = TicketMessage.objects.create(
                    ticket=ticket,
                    author=request.user,
                    message=data.get('message', ''),
                    is_internal=is_internal
                )

                # Update ticket status if appropriate:
                # If customer replies to 'Waiting for Customer', move back to 'In Progress'
                if request.user.role == User.Role.CUSTOMER and ticket.status == SupportTicket.Status.WAITING_FOR_CUSTOMER:
                    ticket.status = SupportTicket.Status.IN_PROGRESS
                    ticket.save()
                elif request.user.role in [User.Role.AGENT, User.Role.ADMIN] and not is_internal:
                    if ticket.status == SupportTicket.Status.OPEN:
                        ticket.status = SupportTicket.Status.IN_PROGRESS
                        ticket.save()

                activity_type = (
                    TicketActivity.ActivityType.NOTE_ADDED
                    if is_internal
                    else TicketActivity.ActivityType.MESSAGE_ADDED
                )
                TicketActivity.objects.create(
                    ticket=ticket,
                    actor=request.user,
                    activity_type=activity_type,
                    details=f"{'Internal note' if is_internal else 'Reply'} added by {request.user.get_full_name()}."
                )

            return Response(
                TicketMessageSerializer(message_obj).data,
                status=status.HTTP_201_CREATED
            )

    @action(detail=True, methods=['get'], url_path='activity')
    def activity(self, request, pk=None):
        """
        GET /tickets/{id}/activity/ -> list activity audit log
        """
        ticket = self.get_object()
        activities = ticket.activities.select_related('actor').order_by('-created_at')
        serializer = TicketActivitySerializer(activities, many=True)
        return Response(serializer.data)
