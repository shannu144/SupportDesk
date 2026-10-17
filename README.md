# SupportDesk — Full-Stack Customer Support Management System

**SupportDesk** is an enterprise-grade, production-style customer support ticket management platform engineered with **Django REST Framework** on the backend and **React (TypeScript + Vite + Tailwind CSS)** on the frontend, backed by **PostgreSQL**.

The platform provides complete role-based support workflows for **Administrators**, **Support Agents**, and **Customers**, including strict authorization boundaries, audit trails, private internal collaboration notes, and real-time database-calculated analytics.

---

## Architecture Overview

```
SupportDesk/
├── backend/
│   ├── config/             # Django project settings, ASGI/WSGI, routing, and Swagger
│   ├── apps/
│   │   ├── accounts/       # Custom User model, JWT auth, RBAC permissions & serializers
│   │   ├── tickets/        # SupportTicket, TicketCategory, TicketMessage, TicketActivity
│   │   └── analytics/      # Aggregation queries for dashboard metrics and trends
│   ├── tests/              # Pytest test suite (16 comprehensive tests)
│   ├── Dockerfile          # Production backend Docker image
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios instance with automatic JWT token refresh
│   │   ├── components/     # Badges, ProtectedRoute, UI modals
│   │   ├── context/        # React AuthContext (JWT session state)
│   │   ├── layouts/        # Modern SaaS sidebar & top navigation layout
│   │   ├── pages/          # Login, Register, Dashboard, Tickets, Detail, Users, Categories
│   │   └── types/          # Strict TypeScript interfaces
│   ├── Dockerfile          # Multi-stage Docker build (Node.js -> Nginx)
│   ├── nginx.conf          # Nginx reverse proxy configuration
│   └── package.json
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI workflow (PostgreSQL, Pytest, Vite build)
├── docker-compose.yml      # Multi-container orchestration (DB, Backend, Frontend)
├── .env.example            # Environment variables template
└── README.md
```

---

## Key Features & Role-Based Access Control

### 1. User Roles & Authorization Boundaries
| Feature / Action | Customer | Support Agent | Administrator |
| :--- | :---: | :---: | :---: |
| Self-Registration & JWT Login | Yes | Yes | Yes |
| Create Support Tickets | Yes | Yes | Yes |
| View Tickets | Own tickets only | All system tickets | All system tickets |
| Add Public Conversation Replies | Yes | Yes | Yes |
| Add Private Internal Notes | No (Strict 403) | Yes | Yes |
| View Private Internal Notes | Hidden from API & UI | Yes | Yes |
| Assign / Reassign Agent | No (Strict 403) | Yes | Yes |
| Update Status / Priority | Reopen eligible | Yes | Yes |
| Manage Categories & Users | No (Strict 403) | No (Strict 403) | Yes |
| Operational Metrics Dashboard | Personal requests | Assigned workload & SLA | Org-wide KPIs & trends |

### 2. Core Modules
- **Ticket Management**: Auto-generated human-readable ticket numbers (`SD-XXXXXX`), priority tags (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), and lifecycle statuses (`OPEN`, `IN_PROGRESS`, `WAITING_FOR_CUSTOMER`, `RESOLVED`, `CLOSED`).
- **Conversations & Notes**: Public thread for customer-agent communication. Staff can toggle **Private Internal Notes**, which are stripped at the database query and serializer levels for customers.
- **Audit History**: Automatic transaction-safe audit logging (`TicketActivity`) capturing timestamp, actor, old status/priority/assignee, and new values.
- **Analytics & SLA**: Real-time calculated KPIs (average resolution time in hours, SLA breaches, 7-day volume trends, agent workload distribution) using database aggregations.
- **OpenAPI / Swagger**: Auto-generated interactive API documentation at `/api/docs/` via `drf-spectacular`.

---

## Technology Stack

- **Backend**: Python 3.12, Django 5.1, Django REST Framework 3.15, SimpleJWT, `django-filter`, `drf-spectacular`, `psycopg2-binary`.
- **Frontend**: React 19, TypeScript, Vite 8, Tailwind CSS v4, React Router v7, Axios, Lucide React, Recharts.
- **Database**: PostgreSQL 16 (with SQLite local fallback for zero-configuration development).
- **DevOps**: Docker, Docker Compose, Nginx, GitHub Actions CI.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ and npm

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Seed test users and sample data
python manage.py seed_data

# Start Django development server
python manage.py runserver 0.0.0.0:8000
```

Backend will be available at: `http://localhost:8000`
- API Root: `http://localhost:8000/api/v1/`
- Swagger UI: `http://localhost:8000/api/docs/`
- Health Check: `http://localhost:8000/api/health/`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Start Vite dev server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## Default Seeded Test Accounts

The `python manage.py seed_data` command creates initial accounts for immediate testing:

| Role | Email | Password | Pre-configured Data |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@supportdesk.local` | `Admin123456!` | Full administrative access, user directory, categories |
| **Support Agent** | `agent.sarah@supportdesk.local` | `Agent123456!` | Technical Support team, active tickets & notes |
| **Support Agent** | `agent.john@supportdesk.local` | `Agent123456!` | Billing & Accounts team, resolved tickets |
| **Customer** | `customer@acmecorp.com` | `Customer123456!` | Acme Corp client account with active tickets |

*Note: The login screen also features one-click buttons to populate credentials for each role instantly.*

---

## Running with Docker Compose

To spin up the complete multi-tier production stack (PostgreSQL, Django API, Nginx React SPA):

```bash
# Clone the repository and copy the environment configuration
cp .env.example .env

# Build and start all containers
docker-compose up --build -d
```

- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/api/v1/`
- **PostgreSQL Database**: `localhost:5432`

---

## Running Automated Tests

### Backend Test Suite (Pytest)
```bash
cd backend
.\venv\Scripts\pytest
```

**Results (16/16 Passed):**
```
tests/test_accounts.py::test_customer_registration PASSED
tests/test_accounts.py::test_registration_password_mismatch PASSED
tests/test_accounts.py::test_jwt_login_success PASSED
tests/test_accounts.py::test_jwt_login_invalid_credentials PASSED
tests/test_accounts.py::test_current_user_profile PASSED
tests/test_accounts.py::test_user_cannot_escalate_role_via_profile_update PASSED
tests/test_accounts.py::test_admin_user_management_restricted_to_admins PASSED
tests/test_tickets.py::test_customer_can_create_ticket PASSED
tests/test_tickets.py::test_customer_cannot_see_other_customer_tickets PASSED
tests/test_tickets.py::test_agent_and_admin_can_view_all_tickets PASSED
tests/test_tickets.py::test_ticket_assignment_by_agent_or_admin PASSED
tests/test_tickets.py::test_customer_cannot_assign_ticket PASSED
tests/test_tickets.py::test_internal_notes_hidden_from_customer PASSED
tests/test_tickets.py::test_reopen_resolved_ticket PASSED
tests/test_tickets.py::test_search_and_filter_tickets PASSED
tests/test_tickets.py::test_dashboard_summary_and_trends PASSED
```

### Frontend Build & Typecheck
```bash
cd frontend
npm run build
```

---

## REST API Specification

### Authentication & Users
- `POST /api/v1/auth/register/` — Register customer account (forces `CUSTOMER` role).
- `POST /api/v1/auth/token/` — Obtain JWT access & refresh tokens with user payload.
- `POST /api/v1/auth/token/refresh/` — Refresh access token.
- `GET /api/v1/auth/me/` — Retrieve authenticated user profile.
- `PATCH /api/v1/auth/me/` — Update profile (role escalation protected).
- `GET /api/v1/users/` — Admin-only user management and role assignment.
- `GET /api/v1/agents/` — List active support agents for ticket assignment.

### Tickets & Categories
- `GET /api/v1/tickets/` — List tickets with search, filtering (`status`, `priority`, `category`), ordering, and pagination.
- `POST /api/v1/tickets/` — Create new ticket.
- `GET /api/v1/tickets/{id}/` — Ticket details with conversation messages and activity history.
- `PATCH /api/v1/tickets/{id}/` — Update ticket status or priority.
- `DELETE /api/v1/tickets/{id}/` — Admin-only deletion.
- `POST /api/v1/tickets/{id}/assign/` — Staff assignment/reassignment.
- `POST /api/v1/tickets/{id}/reopen/` — Reopen eligible resolved/closed ticket.
- `GET /api/v1/tickets/{id}/messages/` — Retrieve message thread (internal notes stripped for customers).
- `POST /api/v1/tickets/{id}/messages/` — Post message or staff internal note.
- `GET /api/v1/tickets/{id}/activity/` — Retrieve audit history trail.
- `GET /api/v1/categories/` — List ticket categories.
- `POST /api/v1/categories/` — Admin create category.

### Analytics & Reports
- `GET /api/v1/dashboard/summary/` — Role-specific KPIs calculated from database.
- `GET /api/v1/dashboard/trends/` — 7-day creation/resolution volume trends and agent workload breakdown.

---

## Production Deployment Checklist

1. Set `DEBUG=0` in `.env`.
2. Generate a secure secret key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
3. Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to your production domain(s).
4. Run `python manage.py collectstatic --noinput`.
5. Run migrations: `python manage.py migrate`.
6. Use Gunicorn behind an Nginx reverse proxy with SSL/TLS (Certbot / Let's Encrypt).
