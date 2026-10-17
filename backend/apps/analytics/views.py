from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, F, Q, ExpressionWrapper, DurationField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from apps.accounts.models import User
from apps.tickets.models import SupportTicket

class DashboardSummaryView(APIView):
    """
    Returns actual calculated metrics based on the requester's role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        base_qs = SupportTicket.objects.all()

        if user.role == User.Role.CUSTOMER:
            # Customer scoped metrics
            cust_qs = base_qs.filter(customer=user)
            total = cust_qs.count()
            open_count = cust_qs.filter(status=SupportTicket.Status.OPEN).count()
            in_progress = cust_qs.filter(status=SupportTicket.Status.IN_PROGRESS).count()
            waiting = cust_qs.filter(status=SupportTicket.Status.WAITING_FOR_CUSTOMER).count()
            resolved = cust_qs.filter(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]).count()

            return Response({
                'role': 'CUSTOMER',
                'total_tickets': total,
                'open_tickets': open_count,
                'in_progress_tickets': in_progress,
                'waiting_tickets': waiting,
                'resolved_tickets': resolved,
            })

        elif user.role == User.Role.AGENT:
            # Agent scoped workload metrics
            assigned_qs = base_qs.filter(assigned_agent=user)
            total_assigned = assigned_qs.count()
            open_assigned = assigned_qs.filter(status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]).count()
            resolved_assigned = assigned_qs.filter(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]).count()
            waiting_cust = assigned_qs.filter(status=SupportTicket.Status.WAITING_FOR_CUSTOMER).count()

            # Overdue tickets
            now = timezone.now()
            overdue_count = assigned_qs.filter(
                due_date__lt=now,
                status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]
            ).count()

            # Agent average resolution time in hours
            resolved_tickets = assigned_qs.filter(
                resolved_at__isnull=False,
                status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]
            )
            durations = [
                (t.resolved_at - t.created_at).total_seconds() / 3600.0
                for t in resolved_tickets
                if t.resolved_at and t.created_at
            ]
            avg_res_hours = round(sum(durations) / len(durations), 1) if durations else 0.0

            return Response({
                'role': 'AGENT',
                'total_assigned': total_assigned,
                'open_assigned': open_assigned,
                'resolved_assigned': resolved_assigned,
                'waiting_customer': waiting_cust,
                'overdue_count': overdue_count,
                'avg_resolution_hours': avg_res_hours,
            })

        else:
            # Admin scoped organization-wide metrics
            total = base_qs.count()
            open_count = base_qs.filter(status=SupportTicket.Status.OPEN).count()
            in_progress = base_qs.filter(status=SupportTicket.Status.IN_PROGRESS).count()
            waiting = base_qs.filter(status=SupportTicket.Status.WAITING_FOR_CUSTOMER).count()
            resolved = base_qs.filter(status=SupportTicket.Status.RESOLVED).count()
            closed = base_qs.filter(status=SupportTicket.Status.CLOSED).count()

            urgent_count = base_qs.filter(
                priority=SupportTicket.Priority.URGENT,
                status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]
            ).count()
            high_count = base_qs.filter(
                priority=SupportTicket.Priority.HIGH,
                status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]
            ).count()

            # Average resolution time across all resolved tickets
            resolved_qs = base_qs.filter(
                resolved_at__isnull=False,
                status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]
            )
            durations = [
                (t.resolved_at - t.created_at).total_seconds() / 3600.0
                for t in resolved_qs
                if t.resolved_at and t.created_at
            ]
            avg_res_hours = round(sum(durations) / len(durations), 1) if durations else 0.0

            # Priority breakdown
            priority_dist = list(base_qs.values('priority').annotate(count=Count('id')))

            # Status breakdown
            status_dist = list(base_qs.values('status').annotate(count=Count('id')))

            return Response({
                'role': 'ADMIN',
                'total_tickets': total,
                'open_tickets': open_count,
                'in_progress_tickets': in_progress,
                'waiting_tickets': waiting,
                'resolved_tickets': resolved,
                'closed_tickets': closed,
                'urgent_tickets': urgent_count,
                'high_tickets': high_count,
                'avg_resolution_hours': avg_res_hours,
                'priority_distribution': priority_dist,
                'status_distribution': status_dist,
            })


class DashboardTrendsView(APIView):
    """
    Returns weekly ticket trends and agent workload for charts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        start_date = now - timedelta(days=7)

        # 7-day trend
        days = []
        for i in range(6, -1, -1):
            day_date = (now - timedelta(days=i)).date()
            day_start = timezone.make_aware(
                timezone.datetime.combine(day_date, timezone.datetime.min.time())
            )
            day_end = timezone.make_aware(
                timezone.datetime.combine(day_date, timezone.datetime.max.time())
            )

            created_count = SupportTicket.objects.filter(
                created_at__range=(day_start, day_end)
            ).count()
            resolved_count = SupportTicket.objects.filter(
                resolved_at__range=(day_start, day_end)
            ).count()

            days.append({
                'date': day_date.strftime('%b %d'),
                'created': created_count,
                'resolved': resolved_count,
            })

        # Agent workload breakdown
        agents = User.objects.filter(role__in=[User.Role.AGENT, User.Role.ADMIN], is_active=True)
        agent_workload = []
        for agent in agents:
            assigned = SupportTicket.objects.filter(assigned_agent=agent)
            active = assigned.filter(status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS]).count()
            resolved = assigned.filter(status__in=[SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED]).count()
            agent_workload.append({
                'agent_id': agent.id,
                'name': agent.get_full_name() or agent.email,
                'active_tickets': active,
                'resolved_tickets': resolved,
            })

        return Response({
            'trends': days,
            'agent_workload': agent_workload,
        })
