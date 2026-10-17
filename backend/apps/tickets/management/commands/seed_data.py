from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.tickets.models import TicketCategory, SupportTicket, TicketMessage, TicketActivity

class Command(BaseCommand):
    help = 'Seeds initial users, categories, sample tickets, messages and activities.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        with transaction.atomic():
            # 1. Admin
            admin, created = User.objects.get_or_create(
                email='admin@supportdesk.local',
                defaults={
                    'first_name': 'Eleanor',
                    'last_name': 'Vance',
                    'role': User.Role.ADMIN,
                    'department': 'Support Leadership',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin.set_password('Admin123456!')
                admin.save()
                self.stdout.write(f"Created Admin: {admin.email}")

            # 2. Agents
            agent1, created = User.objects.get_or_create(
                email='agent.sarah@supportdesk.local',
                defaults={
                    'first_name': 'Sarah',
                    'last_name': 'Connor',
                    'role': User.Role.AGENT,
                    'department': 'Technical Support',
                    'is_staff': True,
                }
            )
            if created:
                agent1.set_password('Agent123456!')
                agent1.save()
                self.stdout.write(f"Created Agent: {agent1.email}")

            agent2, created = User.objects.get_or_create(
                email='agent.john@supportdesk.local',
                defaults={
                    'first_name': 'John',
                    'last_name': 'Miller',
                    'role': User.Role.AGENT,
                    'department': 'Billing & Accounts',
                    'is_staff': True,
                }
            )
            if created:
                agent2.set_password('Agent123456!')
                agent2.save()
                self.stdout.write(f"Created Agent: {agent2.email}")

            # 3. Customer
            customer, created = User.objects.get_or_create(
                email='customer@acmecorp.com',
                defaults={
                    'first_name': 'Marcus',
                    'last_name': 'Aurelius',
                    'role': User.Role.CUSTOMER,
                    'phone_number': '+1 (555) 234-5678',
                }
            )
            if created:
                customer.set_password('Customer123456!')
                customer.save()
                self.stdout.write(f"Created Customer: {customer.email}")

            # 4. Categories
            categories_data = [
                ('Technical Issues', 'Software defects, crash reports, and system performance problems.'),
                ('Billing & Payments', 'Invoices, credit card charges, upgrades and payment receipts.'),
                ('Account Security', 'Password resets, 2FA setup, SSO configuration and permissions.'),
                ('Feature Requests', 'Product suggestions and enhancement ideas from users.'),
            ]
            cats = {}
            for name, desc in categories_data:
                c, _ = TicketCategory.objects.get_or_create(name=name, defaults={'description': desc})
                cats[name] = c

            # 5. Tickets with realistic data
            now = timezone.now()
            
            # Ticket 1: Open technical ticket
            t1, created1 = SupportTicket.objects.get_or_create(
                subject='Unable to export monthly analytics report to CSV',
                customer=customer,
                defaults={
                    'description': 'Whenever I click the "Export CSV" button on the billing dashboard, it shows a 504 gateway timeout error.',
                    'category': cats['Technical Issues'],
                    'priority': SupportTicket.Priority.HIGH,
                    'status': SupportTicket.Status.OPEN,
                    'tags': 'reports,timeout,csv',
                    'due_date': now + timedelta(days=1),
                }
            )
            if created1:
                TicketActivity.objects.create(
                    ticket=t1,
                    actor=customer,
                    activity_type=TicketActivity.ActivityType.CREATED,
                    details='Ticket created by customer via portal.'
                )

            # Ticket 2: In Progress assigned to agent Sarah
            t2, created2 = SupportTicket.objects.get_or_create(
                subject='SSO SAML authentication loop on Chrome browsers',
                customer=customer,
                defaults={
                    'description': 'Our team members using Google Chrome cannot complete SAML 2.0 authentication; it keeps redirecting back to the login screen.',
                    'category': cats['Account Security'],
                    'priority': SupportTicket.Priority.URGENT,
                    'status': SupportTicket.Status.IN_PROGRESS,
                    'assigned_agent': agent1,
                    'tags': 'security,sso,saml,urgent',
                    'due_date': now + timedelta(hours=8),
                }
            )
            if created2:
                TicketActivity.objects.create(
                    ticket=t2,
                    actor=customer,
                    activity_type=TicketActivity.ActivityType.CREATED,
                    details='Ticket created with URGENT priority.'
                )
                TicketActivity.objects.create(
                    ticket=t2,
                    actor=admin,
                    activity_type=TicketActivity.ActivityType.ASSIGNMENT_CHANGE,
                    old_value='Unassigned',
                    new_value=agent1.get_full_name(),
                    details='Assigned to Sarah Connor for immediate investigation.'
                )
                # Public reply by agent
                TicketMessage.objects.create(
                    ticket=t2,
                    author=agent1,
                    message='Hello Marcus, I am looking into your Okta/SAML configuration right now. Could you please share the exact domain URL being redirected?',
                    is_internal=False
                )
                # Internal note by agent
                TicketMessage.objects.create(
                    ticket=t2,
                    author=agent1,
                    message='[INTERNAL NOTE] Checked auth log: Looks like ACS URL certificate fingerprint expired yesterday.',
                    is_internal=True
                )

            # Ticket 3: Resolved billing ticket
            t3, created3 = SupportTicket.objects.get_or_create(
                subject='Duplicate charge on invoice INV-2026-8812',
                customer=customer,
                defaults={
                    'description': 'We were charged twice on October 1st for the Enterprise plan seat expansion.',
                    'category': cats['Billing & Payments'],
                    'priority': SupportTicket.Priority.MEDIUM,
                    'status': SupportTicket.Status.RESOLVED,
                    'assigned_agent': agent2,
                    'tags': 'billing,refund',
                    'resolved_at': now - timedelta(hours=2),
                }
            )
            if created3:
                TicketActivity.objects.create(
                    ticket=t3,
                    actor=customer,
                    activity_type=TicketActivity.ActivityType.CREATED,
                    details='Billing dispute ticket submitted.'
                )
                TicketMessage.objects.create(
                    ticket=t3,
                    author=agent2,
                    message='Hi Marcus, I have processed a full refund of $450 back to your company Visa card ending in 4119. Please allow 2-3 business days to appear on your bank statement.',
                    is_internal=False
                )
                TicketActivity.objects.create(
                    ticket=t3,
                    actor=agent2,
                    activity_type=TicketActivity.ActivityType.STATUS_CHANGE,
                    old_value=SupportTicket.Status.IN_PROGRESS,
                    new_value=SupportTicket.Status.RESOLVED,
                    details='Refund processed and ticket marked as resolved.'
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with test data!'))
