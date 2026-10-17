from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.tickets.models import TicketCategory, SupportTicket, TicketMessage, TicketActivity

class TicketCategorySerializer(serializers.ModelSerializer):
    ticket_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = TicketCategory
        fields = ('id', 'name', 'description', 'is_active', 'ticket_count', 'created_at')


class TicketMessageSerializer(serializers.ModelSerializer):
    author_detail = UserSerializer(source='author', read_only=True)

    class Meta:
        model = TicketMessage
        fields = (
            'id',
            'ticket',
            'author',
            'author_detail',
            'message',
            'is_internal',
            'created_at',
        )
        read_only_fields = ('id', 'ticket', 'author', 'created_at')


class TicketActivitySerializer(serializers.ModelSerializer):
    actor_detail = UserSerializer(source='actor', read_only=True)

    class Meta:
        model = TicketActivity
        fields = (
            'id',
            'ticket',
            'actor',
            'actor_detail',
            'activity_type',
            'old_value',
            'new_value',
            'details',
            'created_at',
        )
        read_only_fields = ('id', 'ticket', 'actor', 'created_at')


class SupportTicketListSerializer(serializers.ModelSerializer):
    customer_detail = UserSerializer(source='customer', read_only=True)
    assigned_agent_detail = UserSerializer(source='assigned_agent', read_only=True)
    category_detail = TicketCategorySerializer(source='category', read_only=True)
    messages_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = SupportTicket
        fields = (
            'id',
            'ticket_number',
            'subject',
            'priority',
            'status',
            'category',
            'category_detail',
            'customer',
            'customer_detail',
            'assigned_agent',
            'assigned_agent_detail',
            'tags',
            'due_date',
            'resolved_at',
            'created_at',
            'updated_at',
            'messages_count',
        )


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    customer_detail = UserSerializer(source='customer', read_only=True)
    assigned_agent_detail = UserSerializer(source='assigned_agent', read_only=True)
    category_detail = TicketCategorySerializer(source='category', read_only=True)
    messages = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = (
            'id',
            'ticket_number',
            'subject',
            'description',
            'priority',
            'status',
            'category',
            'category_detail',
            'customer',
            'customer_detail',
            'assigned_agent',
            'assigned_agent_detail',
            'tags',
            'due_date',
            'resolved_at',
            'created_at',
            'updated_at',
            'messages',
            'activities',
        )
        read_only_fields = ('id', 'ticket_number', 'customer', 'resolved_at', 'created_at', 'updated_at')

    def get_messages(self, obj):
        user = self.context['request'].user
        # Internal notes are strictly stripped for customers!
        messages_qs = obj.messages.all().select_related('author')
        if not (user.is_staff or user.role in ['ADMIN', 'AGENT'] or user.is_superuser):
            messages_qs = messages_qs.filter(is_internal=False)
        return TicketMessageSerializer(messages_qs, many=True).data

    def get_activities(self, obj):
        # Return recent activity history for ticket
        activities_qs = obj.activities.all().select_related('actor')[:25]
        return TicketActivitySerializer(activities_qs, many=True).data


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = (
            'id',
            'ticket_number',
            'subject',
            'description',
            'category',
            'priority',
            'tags',
            'due_date',
        )
        read_only_fields = ('id', 'ticket_number')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['customer'] = user
        validated_data['status'] = SupportTicket.Status.OPEN
        return super().create(validated_data)


class TicketAssignSerializer(serializers.Serializer):
    assigned_agent_id = serializers.IntegerField(required=True, allow_null=True)
