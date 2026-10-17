import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.tickets.models import TicketCategory, SupportTicket, TicketMessage, TicketActivity

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@example.com',
        password='AdminPassword123!',
        first_name='Admin',
        last_name='User',
        role=User.Role.ADMIN
    )

@pytest.fixture
def agent_user(db):
    return User.objects.create_user(
        email='agent@example.com',
        password='AgentPassword123!',
        first_name='Agent',
        last_name='Smith',
        role=User.Role.AGENT
    )

@pytest.fixture
def second_agent(db):
    return User.objects.create_user(
        email='agent2@example.com',
        password='AgentPassword123!',
        first_name='Agent',
        last_name='Jones',
        role=User.Role.AGENT
    )

@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        email='customer@example.com',
        password='CustomerPassword123!',
        first_name='Alice',
        last_name='Customer',
        role=User.Role.CUSTOMER
    )

@pytest.fixture
def other_customer(db):
    return User.objects.create_user(
        email='other@example.com',
        password='CustomerPassword123!',
        first_name='Bob',
        last_name='Other',
        role=User.Role.CUSTOMER
    )

@pytest.fixture
def category(db):
    return TicketCategory.objects.create(name='Technical Support', description='Hardware and software issues')

@pytest.fixture
def sample_ticket(db, customer_user, category):
    return SupportTicket.objects.create(
        subject='Cannot connect to VPN',
        description='VPN connection drops every 5 minutes.',
        customer=customer_user,
        category=category,
        priority=SupportTicket.Priority.HIGH,
        status=SupportTicket.Status.OPEN
    )

@pytest.mark.django_db
class TestTicketLifecycleAndPermissions:
    def test_customer_can_create_ticket(self, api_client, customer_user, category):
        api_client.force_authenticate(user=customer_user)
        payload = {
            'subject': 'Billing discrepancy on invoice #102',
            'description': 'I noticed an extra charge on my bill.',
            'category': category.id,
            'priority': 'MEDIUM',
            'tags': 'billing,invoice'
        }
        response = api_client.post('/api/v1/tickets/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == payload['subject']
        assert response.data['ticket_number'].startswith('SD-')

        # Check activity was recorded
        ticket_id = response.data['id']
        activities = TicketActivity.objects.filter(ticket_id=ticket_id)
        assert activities.filter(activity_type=TicketActivity.ActivityType.CREATED).exists()

    def test_customer_cannot_see_other_customer_tickets(self, api_client, other_customer, sample_ticket):
        api_client.force_authenticate(user=other_customer)
        # Listing tickets
        res_list = api_client.get('/api/v1/tickets/')
        assert res_list.status_code == status.HTTP_200_OK
        ticket_ids = [t['id'] for t in res_list.data['results']]
        assert sample_ticket.id not in ticket_ids

        # Direct retrieval
        res_detail = api_client.get(f'/api/v1/tickets/{sample_ticket.id}/')
        assert res_detail.status_code == status.HTTP_404_NOT_FOUND or res_detail.status_code == status.HTTP_403_FORBIDDEN

    def test_agent_and_admin_can_view_all_tickets(self, api_client, agent_user, admin_user, sample_ticket):
        for user in [agent_user, admin_user]:
            api_client.force_authenticate(user=user)
            res = api_client.get('/api/v1/tickets/')
            assert res.status_code == status.HTTP_200_OK
            ticket_ids = [t['id'] for t in res.data['results']]
            assert sample_ticket.id in ticket_ids

    def test_ticket_assignment_by_agent_or_admin(self, api_client, admin_user, second_agent, sample_ticket):
        api_client.force_authenticate(user=admin_user)
        assign_url = f'/api/v1/tickets/{sample_ticket.id}/assign/'
        res = api_client.post(assign_url, {'assigned_agent_id': second_agent.id}, format='json')
        assert res.status_code == status.HTTP_200_OK
        sample_ticket.refresh_from_db()
        assert sample_ticket.assigned_agent == second_agent
        # Status automatically moved to IN_PROGRESS upon assignment
        assert sample_ticket.status == SupportTicket.Status.IN_PROGRESS

        # Activity was created
        activity = TicketActivity.objects.filter(
            ticket=sample_ticket,
            activity_type=TicketActivity.ActivityType.ASSIGNMENT_CHANGE
        ).first()
        assert activity is not None

    def test_customer_cannot_assign_ticket(self, api_client, customer_user, second_agent, sample_ticket):
        api_client.force_authenticate(user=customer_user)
        assign_url = f'/api/v1/tickets/{sample_ticket.id}/assign/'
        res = api_client.post(assign_url, {'assigned_agent_id': second_agent.id}, format='json')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_internal_notes_hidden_from_customer(self, api_client, admin_user, customer_user, sample_ticket):
        # Admin posts internal note
        api_client.force_authenticate(user=admin_user)
        msg_url = f'/api/v1/tickets/{sample_ticket.id}/messages/'
        note_res = api_client.post(msg_url, {
            'message': 'Internal note: Customer account has high churn risk.',
            'is_internal': True
        }, format='json')
        assert note_res.status_code == status.HTTP_201_CREATED

        # Customer attempts to view messages
        api_client.force_authenticate(user=customer_user)
        get_res = api_client.get(msg_url)
        assert get_res.status_code == status.HTTP_200_OK
        messages = get_res.data
        assert len(messages) == 0  # Internal note not returned

        # Customer cannot submit internal notes
        bad_post = api_client.post(msg_url, {
            'message': 'Customer tries to make private note',
            'is_internal': True
        }, format='json')
        assert bad_post.status_code == status.HTTP_403_FORBIDDEN

    def test_reopen_resolved_ticket(self, api_client, customer_user, sample_ticket):
        # Resolve ticket
        sample_ticket.status = SupportTicket.Status.RESOLVED
        sample_ticket.save()

        api_client.force_authenticate(user=customer_user)
        reopen_url = f'/api/v1/tickets/{sample_ticket.id}/reopen/'
        res = api_client.post(reopen_url)
        assert res.status_code == status.HTTP_200_OK
        sample_ticket.refresh_from_db()
        assert sample_ticket.status == SupportTicket.Status.OPEN
        assert sample_ticket.resolved_at is None

    def test_search_and_filter_tickets(self, api_client, admin_user, sample_ticket):
        api_client.force_authenticate(user=admin_user)
        # Search by ticket subject
        res = api_client.get('/api/v1/tickets/?search=VPN')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data['results']) >= 1

        # Filter by priority
        res_priority = api_client.get('/api/v1/tickets/?priority=HIGH')
        assert res_priority.status_code == status.HTTP_200_OK
        assert len(res_priority.data['results']) >= 1

        res_none = api_client.get('/api/v1/tickets/?priority=LOW')
        assert res_none.status_code == status.HTTP_200_OK
        assert len(res_none.data['results']) == 0

    def test_dashboard_summary_and_trends(self, api_client, admin_user, agent_user, customer_user, sample_ticket):
        # Admin metrics
        api_client.force_authenticate(user=admin_user)
        admin_dash = api_client.get('/api/v1/dashboard/summary/')
        assert admin_dash.status_code == status.HTTP_200_OK
        assert admin_dash.data['role'] == 'ADMIN'
        assert admin_dash.data['total_tickets'] >= 1

        # Trends
        trends = api_client.get('/api/v1/dashboard/trends/')
        assert trends.status_code == status.HTTP_200_OK
        assert 'trends' in trends.data
        assert 'agent_workload' in trends.data

        # Customer metrics
        api_client.force_authenticate(user=customer_user)
        cust_dash = api_client.get('/api/v1/dashboard/summary/')
        assert cust_dash.status_code == status.HTTP_200_OK
        assert cust_dash.data['role'] == 'CUSTOMER'
        assert cust_dash.data['total_tickets'] >= 1
