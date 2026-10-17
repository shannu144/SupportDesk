export type UserRole = 'ADMIN' | 'AGENT' | 'CUSTOMER';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  phone_number?: string;
  department?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'WAITING_FOR_CUSTOMER' | 'RESOLVED' | 'CLOSED';

export interface TicketCategory {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  ticket_count?: number;
  created_at: string;
}

export interface TicketMessage {
  id: number;
  ticket: number;
  author: number;
  author_detail: User;
  message: string;
  is_internal: boolean;
  created_at: string;
}

export interface TicketActivity {
  id: number;
  ticket: number;
  actor?: number;
  actor_detail?: User;
  activity_type: string;
  old_value?: string;
  new_value?: string;
  details: string;
  created_at: string;
}

export interface SupportTicket {
  id: number;
  ticket_number: string;
  subject: string;
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  category?: number;
  category_detail?: TicketCategory;
  customer: number;
  customer_detail: User;
  assigned_agent?: number;
  assigned_agent_detail?: User;
  tags?: string;
  due_date?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  messages_count?: number;
  messages?: TicketMessage[];
  activities?: TicketActivity[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface DashboardSummary {
  role: UserRole;
  total_tickets?: number;
  open_tickets?: number;
  in_progress_tickets?: number;
  waiting_tickets?: number;
  resolved_tickets?: number;
  closed_tickets?: number;
  urgent_tickets?: number;
  high_tickets?: number;
  avg_resolution_hours?: number;
  // Agent specific
  total_assigned?: number;
  open_assigned?: number;
  resolved_assigned?: number;
  waiting_customer?: number;
  overdue_count?: number;
  // Admin distributions
  priority_distribution?: { priority: TicketPriority; count: number }[];
  status_distribution?: { status: TicketStatus; count: number }[];
}

export interface DashboardTrends {
  trends: { date: string; created: number; resolved: number }[];
  agent_workload: {
    agent_id: number;
    name: string;
    active_tickets: number;
    resolved_tickets: number;
  }[];
}
