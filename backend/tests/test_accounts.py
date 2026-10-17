import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User

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
    user = User.objects.create_user(
        email='agent@example.com',
        password='AgentPassword123!',
        first_name='Agent',
        last_name='Support',
        role=User.Role.AGENT
    )
    return user

@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        email='customer@example.com',
        password='CustomerPassword123!',
        first_name='Jane',
        last_name='Doe',
        role=User.Role.CUSTOMER
    )

@pytest.mark.django_db
class TestAuthenticationAndPermissions:
    def test_customer_registration(self, api_client):
        url = '/api/v1/auth/register/'
        payload = {
            'email': 'newcustomer@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'first_name': 'New',
            'last_name': 'Customer',
            'phone_number': '+1234567890'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newcustomer@example.com'

        # Ensure user created in database is forced to CUSTOMER role
        user = User.objects.get(email='newcustomer@example.com')
        assert user.role == User.Role.CUSTOMER
        assert user.check_password('SecurePassword123!')

    def test_registration_password_mismatch(self, api_client):
        url = '/api/v1/auth/register/'
        payload = {
            'email': 'badpass@example.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword123!',
            'first_name': 'Bad',
            'last_name': 'Pass'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_jwt_login_success(self, api_client, customer_user):
        url = '/api/v1/auth/token/'
        payload = {
            'email': customer_user.email,
            'password': 'CustomerPassword123!'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['email'] == customer_user.email
        assert response.data['user']['role'] == User.Role.CUSTOMER

    def test_jwt_login_invalid_credentials(self, api_client, customer_user):
        url = '/api/v1/auth/token/'
        payload = {
            'email': customer_user.email,
            'password': 'WrongPassword123!'
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_profile(self, api_client, customer_user):
        api_client.force_authenticate(user=customer_user)
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == customer_user.email

    def test_user_cannot_escalate_role_via_profile_update(self, api_client, customer_user):
        api_client.force_authenticate(user=customer_user)
        # Attempt to change role to ADMIN
        response = api_client.patch('/api/v1/auth/me/', {'role': 'ADMIN', 'first_name': 'Hacker'})
        assert response.status_code == status.HTTP_200_OK

        customer_user.refresh_from_db()
        assert customer_user.role == User.Role.CUSTOMER  # Role untouched
        assert customer_user.first_name == 'Hacker'

    def test_admin_user_management_restricted_to_admins(self, api_client, agent_user, customer_user, admin_user):
        # Customer cannot access /api/v1/users/
        api_client.force_authenticate(user=customer_user)
        assert api_client.get('/api/v1/users/').status_code == status.HTTP_403_FORBIDDEN

        # Agent cannot access /api/v1/users/
        api_client.force_authenticate(user=agent_user)
        assert api_client.get('/api/v1/users/').status_code == status.HTTP_403_FORBIDDEN

        # Admin can access /api/v1/users/
        api_client.force_authenticate(user=admin_user)
        res = api_client.get('/api/v1/users/')
        assert res.status_code == status.HTTP_200_OK
