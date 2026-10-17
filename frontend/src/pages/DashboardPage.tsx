import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { DashboardSummary, DashboardTrends } from '../types';
import {
  Ticket,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { Link } from 'react-router-dom';

const PRIORITY_COLORS: Record<string, string> = {
  LOW: '#10b981',
  MEDIUM: '#3b82f6',
  HIGH: '#f59e0b',
  URGENT: '#ef4444',
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<DashboardTrends | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const [sumRes, trendRes] = await Promise.all([
          apiClient.get<DashboardSummary>('/dashboard/summary/'),
          apiClient.get<DashboardTrends>('/dashboard/trends/'),
        ]);
        setSummary(sumRes.data);
        setTrends(trendRes.data);
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, {user?.first_name || user?.email}!
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {user?.role === 'ADMIN' && 'Here is the real-time operational overview of the entire support desk.'}
            {user?.role === 'AGENT' && 'Here is your current workload, assigned queues, and resolution performance.'}
            {user?.role === 'CUSTOMER' && 'Track and manage all your active and resolved support requests.'}
          </p>
        </div>
        <div>
          <Link
            to="/tickets"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
          >
            <Ticket className="h-4 w-4" />
            {user?.role === 'CUSTOMER' ? 'Submit or View Tickets' : 'Go to Ticket Queue'}
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Customer Metrics */}
        {user?.role === 'CUSTOMER' && (
          <>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Total Tickets</span>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  <Ticket className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.total_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Open Tickets</span>
                <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                  <Clock className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.open_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">In Progress</span>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <TrendingUp className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.in_progress_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Resolved</span>
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.resolved_tickets || 0}</p>
            </div>
          </>
        )}

        {/* Agent Metrics */}
        {user?.role === 'AGENT' && (
          <>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">My Assigned Tickets</span>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Ticket className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.total_assigned || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Active Workload</span>
                <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                  <Clock className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.open_assigned || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Overdue / SLA Alert</span>
                <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                  <AlertTriangle className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-rose-600 mt-3">{summary?.overdue_count || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Avg Resolution Time</span>
                <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">
                {summary?.avg_resolution_hours || 0} <span className="text-base font-normal text-slate-500">hrs</span>
              </p>
            </div>
          </>
        )}

        {/* Admin Metrics */}
        {user?.role === 'ADMIN' && (
          <>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Total System Tickets</span>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Ticket className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.total_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Urgent Tickets</span>
                <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                  <Flame className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-rose-600 mt-3">{summary?.urgent_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">In Progress</span>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  <Clock className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">{summary?.in_progress_tickets || 0}</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-500">Avg Resolution Time</span>
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900 mt-3">
                {summary?.avg_resolution_hours || 0} <span className="text-base font-normal text-slate-500">hrs</span>
              </p>
            </div>
          </>
        )}
      </div>

      {/* Analytics Charts (For Admins and Agents) */}
      {user?.role !== 'CUSTOMER' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Trend Bar Chart */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-indigo-600" />
              Ticket Activity Trend (Last 7 Days)
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trends?.trends || []}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                  />
                  <Bar dataKey="created" name="New Tickets" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="resolved" name="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Agent Workload Table / Chart */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Ticket className="h-5 w-5 text-indigo-600" />
              Agent Workload & Performance
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-semibold uppercase text-slate-400">
                    <th className="pb-3">Support Agent</th>
                    <th className="pb-3 text-center">Active Queue</th>
                    <th className="pb-3 text-center">Resolved</th>
                    <th className="pb-3 text-right">Performance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {trends?.agent_workload.map((agent) => (
                    <tr key={agent.agent_id} className="hover:bg-slate-50/50">
                      <td className="py-3 font-medium text-slate-900">{agent.name}</td>
                      <td className="py-3 text-center">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          {agent.active_tickets}
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {agent.resolved_tickets}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <span className="text-xs text-slate-500">
                          {agent.active_tickets + agent.resolved_tickets > 0 ? 'Active' : 'Standby'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
