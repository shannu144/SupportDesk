import React from 'react';
import { TicketPriority, TicketStatus } from '../types';

export const PriorityBadge: React.FC<{ priority: TicketPriority }> = ({ priority }) => {
  const styles: Record<TicketPriority, { bg: string; text: string; dot: string }> = {
    LOW: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', text: 'Low', dot: 'bg-emerald-500' },
    MEDIUM: { bg: 'bg-blue-50 text-blue-700 border-blue-200', text: 'Medium', dot: 'bg-blue-500' },
    HIGH: { bg: 'bg-amber-50 text-amber-700 border-amber-200', text: 'High', dot: 'bg-amber-500' },
    URGENT: { bg: 'bg-rose-50 text-rose-700 border-rose-200', text: 'Urgent', dot: 'bg-rose-500' },
  };

  const style = styles[priority] || styles.MEDIUM;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${style.bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      {style.text}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: TicketStatus }> = ({ status }) => {
  const styles: Record<TicketStatus, { bg: string; text: string }> = {
    OPEN: { bg: 'bg-sky-50 text-sky-700 border-sky-200', text: 'Open' },
    IN_PROGRESS: { bg: 'bg-indigo-50 text-indigo-700 border-indigo-200', text: 'In Progress' },
    WAITING_FOR_CUSTOMER: { bg: 'bg-purple-50 text-purple-700 border-purple-200', text: 'Waiting Customer' },
    RESOLVED: { bg: 'bg-teal-50 text-teal-700 border-teal-200', text: 'Resolved' },
    CLOSED: { bg: 'bg-slate-100 text-slate-700 border-slate-200', text: 'Closed' },
  };

  const style = styles[status] || styles.OPEN;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${style.bg}`}
    >
      {style.text}
    </span>
  );
};

export const RoleBadge: React.FC<{ role: string }> = ({ role }) => {
  const styles: Record<string, string> = {
    ADMIN: 'bg-red-50 text-red-700 border-red-200',
    AGENT: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    CUSTOMER: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
        styles[role] || 'bg-slate-100 text-slate-700'
      }`}
    >
      {role}
    </span>
  );
};
