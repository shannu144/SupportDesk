import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class TicketCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Ticket Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupportTicket(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WAITING_FOR_CUSTOMER = 'WAITING_FOR_CUSTOMER', 'Waiting for Customer'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    ticket_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_tickets',
        db_index=True
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        db_index=True
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        db_index=True
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True
    )

    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    due_date = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['assigned_agent', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate readable ticket number: SD-XXXXXX
            random_hex = uuid.uuid4().hex[:6].upper()
            self.ticket_number = f"SD-{random_hex}"
        
        # Automatically record resolution time
        if self.status in [self.Status.RESOLVED, self.Status.CLOSED] and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status in [self.Status.OPEN, self.Status.IN_PROGRESS, self.Status.WAITING_FOR_CUSTOMER]:
            # If reopened
            if self.resolved_at:
                self.resolved_at = None

        super().save(*args, **kwargs)


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_messages'
    )
    message = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal notes are visible only to support staff and admins."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        note_tag = " [INTERNAL]" if self.is_internal else ""
        return f"Message by {self.author} on {self.ticket.ticket_number}{note_tag}"


class TicketActivity(models.Model):
    class ActivityType(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Changed'
        PRIORITY_CHANGE = 'PRIORITY_CHANGE', 'Priority Changed'
        ASSIGNMENT_CHANGE = 'ASSIGNMENT_CHANGE', 'Assignment Changed'
        MESSAGE_ADDED = 'MESSAGE_ADDED', 'Message Added'
        NOTE_ADDED = 'NOTE_ADDED', 'Internal Note Added'
        REOPENED = 'REOPENED', 'Ticket Reopened'
        UPDATED = 'UPDATED', 'Ticket Updated'

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='activities',
        db_index=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_activities'
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
        db_index=True
    )
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} on {self.ticket.ticket_number} by {self.actor}"
