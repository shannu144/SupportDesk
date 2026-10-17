from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import User
from apps.accounts.serializers import (
    UserSerializer,
    RegisterSerializer,
    ProfileUpdateSerializer,
    AdminUserManagementSerializer,
)
from apps.accounts.permissions import IsAdminUserRole, IsAgentUserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer to include user details (role, email, name) in token payload.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include serialized user info in the login response
        data['user'] = UserSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the currently authenticated user's profile.
    Changing email or role is strictly forbidden through this endpoint.
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProfileUpdateSerializer
        return UserSerializer


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only management of system users (Admins, Agents, Customers).
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = AdminUserManagementSerializer
    permission_classes = [IsAdminUserRole]
    search_fields = ['email', 'first_name', 'last_name', 'department']
    filterset_fields = ['role', 'is_active', 'department']


class AgentListView(generics.ListAPIView):
    """
    List active agents and admins for ticket assignment.
    Restricted to Agents and Admins.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAgentUserRole]

    def get_queryset(self):
        return User.objects.filter(
            role__in=[User.Role.AGENT, User.Role.ADMIN],
            is_active=True
        ).order_by('first_name', 'last_name')
