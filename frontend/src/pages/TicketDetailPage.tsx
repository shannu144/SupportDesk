import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  SupportTicket,
  TicketMessage,
  TicketActivity,
  TicketPriority,
  TicketStatus,
  User as UserType,
} from '../types';
import { PriorityBadge, StatusBadge, RoleBadge } from '../components/Badges';
import {
  ArrowLeft,
  Send,
  Lock,
  UserCheck,
  RotateCcw,
  Clock,
  History,
  MessageSquare,
  AlertCircle,
  Tag,
  CheckCircle,
} from 'lucide-react';

export const TicketDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [agents, setAgents] = useState<UserType[]>([]);
  const [loading, setLoading] = useState(true);
  const [replyText, setReplyText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submittingReply, setSubmittingReply] = useState(false);
  const [updatingTicket, setUpdatingTicket] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'conversation' | 'activity'>('conversation');
  const [error, setError] = useState<string | null>(null);

  const fetchTicket = async () => {
    try {
      const res = await apiClient.get<SupportTicket>(`/tickets/${id}/`);
      setTicket(res.data);
      setSelectedAgent(res.data.assigned_agent?.toString() || '');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load ticket details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();

    if (user?.role !== 'CUSTOMER') {
      apiClient.get<UserType[]>('/agents/').then((res) => {
        setAgents(res.data);
      }).catch(console.error);
    }
  }, [id, user]);

  const handlePostMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim()) return;

    setSubmittingReply(true);
    try {
      await apiClient.post(`/tickets/${id}/messages/`, {
        message: replyText,
        is_internal: isInternal,
      });
      setReplyText('');
      setIsInternal(false);
      await fetchTicket();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to post message.');
    } finally {
      setSubmittingReply(false);
    }
  };

  const handleStatusChange = async (newStatus: TicketStatus) => {
    setUpdatingTicket(true);
    try {
      await apiClient.patch(`/tickets/${id}/`, { status: newStatus });
      await fetchTicket();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status.');
    } finally {
      setUpdatingTicket(false);
    }
  };

  const handlePriorityChange = async (newPriority: TicketPriority) => {
    setUpdatingTicket(true);
    try {
      await apiClient.patch(`/tickets/${id}/`, { priority: newPriority });
      await fetchTicket();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update priority.');
    } finally {
      setUpdatingTicket(false);
    }
  };

  const handleAssignAgent = async () => {
    setUpdatingTicket(true);
    try {
      const agentId = selectedAgent ? parseInt(selectedAgent, 10) : null;
      await apiClient.post(`/tickets/${id}/assign/`, { assigned_agent_id: agentId });
      await fetchTicket();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to assign ticket.');
    } finally {
      setUpdatingTicket(false);
    }
  };

  const handleReopen = async () => {
    setUpdatingTicket(true);
    try {
      await apiClient.post(`/tickets/${id}/reopen/`);
      await fetchTicket();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reopen ticket.');
    } finally {
      setUpdatingTicket(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-white rounded-2xl border border-slate-200 text-center">
        <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-800">Unable to load ticket</h2>
        <p className="text-sm text-slate-500 mt-1">{error || 'Ticket not found or unauthorized.'}</p>
        <button
          onClick={() => navigate('/tickets')}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium"
        >
          Return to tickets
        </button>
      </div>
    );
  }

  const isStaff = user?.role === 'ADMIN' || user?.role === 'AGENT';
  const canReopen =
    (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') &&
    (user?.role === 'CUSTOMER' || isStaff);

  return (
    <div className="space-y-6">
      {/* Top back button and action bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/tickets')}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Tickets
        </button>

        <div className="flex items-center gap-2">
          {canReopen && (
            <button
              onClick={handleReopen}
              disabled={updatingTicket}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 text-xs font-semibold transition-colors disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              Reopen Ticket
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Ticket Thread & Meta Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Details & Conversation Thread */}
        <div className="lg:col-span-2 space-y-6">
          {/* Header Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                {ticket.ticket_number}
              </span>
              <div className="flex items-center gap-2">
                <StatusBadge status={ticket.status} />
                <PriorityBadge priority={ticket.priority} />
              </div>
            </div>

            <h1 className="text-xl font-bold text-slate-900 mt-3">{ticket.subject}</h1>

            <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
              {ticket.description}
            </div>

            {ticket.tags && (
              <div className="mt-4 flex items-center gap-2 flex-wrap">
                <Tag className="h-3.5 w-3.5 text-slate-400" />
                {ticket.tags.split(',').map((tag, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md font-mono"
                  >
                    #{tag.trim()}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Conversation and Activity Tabs */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="border-b border-slate-200 px-6 flex items-center gap-6">
              <button
                onClick={() => setActiveTab('conversation')}
                className={`py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
                  activeTab === 'conversation'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <MessageSquare className="h-4 w-4" />
                Conversation ({ticket.messages?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('activity')}
                className={`py-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
                  activeTab === 'activity'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <History className="h-4 w-4" />
                Activity History ({ticket.activities?.length || 0})
              </button>
            </div>

            {/* Tab: Conversation */}
            {activeTab === 'conversation' && (
              <div className="p-6 space-y-6">
                {ticket.messages && ticket.messages.length > 0 ? (
                  <div className="space-y-4">
                    {ticket.messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`p-4 rounded-xl border transition-all ${
                          msg.is_internal
                            ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                            : msg.author_detail?.role === 'CUSTOMER'
                            ? 'bg-white border-slate-200'
                            : 'bg-indigo-50/50 border-indigo-100'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-slate-900">
                              {msg.author_detail?.full_name || msg.author_detail?.email}
                            </span>
                            <RoleBadge role={msg.author_detail?.role || 'CUSTOMER'} />
                            {msg.is_internal && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                                <Lock className="h-3 w-3" />
                                Internal Staff Note
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-slate-400">
                            {new Date(msg.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">
                          {msg.message}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400 text-center py-6">
                    No replies or notes posted yet. Start the conversation below.
                  </p>
                )}

                {/* Reply Form */}
                <form onSubmit={handlePostMessage} className="mt-6 pt-6 border-t border-slate-200 space-y-4">
                  {isStaff && (
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="isInternal"
                        checked={isInternal}
                        onChange={(e) => setIsInternal(e.target.checked)}
                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                      />
                      <label
                        htmlFor="isInternal"
                        className="text-xs font-semibold text-amber-800 flex items-center gap-1"
                      >
                        <Lock className="h-3 w-3" />
                        Private Internal Note (Hidden from Customer)
                      </label>
                    </div>
                  )}

                  <div>
                    <textarea
                      required
                      rows={4}
                      placeholder={
                        isInternal
                          ? 'Write an internal investigation note for support staff...'
                          : 'Type your reply to the customer...'
                      }
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      className={`w-full p-3.5 rounded-xl border text-sm focus:outline-none focus:ring-2 shadow-sm ${
                        isInternal
                          ? 'border-amber-300 bg-amber-50/30 focus:ring-amber-500'
                          : 'border-slate-300 focus:ring-indigo-500'
                      }`}
                    />
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={submittingReply || !replyText.trim()}
                      className={`inline-flex items-center gap-2 px-5 py-2 rounded-lg text-white text-sm font-semibold shadow-sm transition-colors disabled:opacity-50 ${
                        isInternal
                          ? 'bg-amber-600 hover:bg-amber-700'
                          : 'bg-indigo-600 hover:bg-indigo-700'
                      }`}
                    >
                      {submittingReply ? 'Posting...' : isInternal ? 'Post Internal Note' : 'Send Reply'}
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Tab: Activity History */}
            {activeTab === 'activity' && (
              <div className="p-6">
                <div className="flow-root">
                  <ul className="-mb-8">
                    {ticket.activities?.map((act, actIdx) => (
                      <li key={act.id}>
                        <div className="relative pb-8">
                          {actIdx !== (ticket.activities?.length || 0) - 1 ? (
                            <span
                              className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200"
                              aria-hidden="true"
                            />
                          ) : null}
                          <div className="relative flex space-x-3">
                            <div>
                              <span className="h-8 w-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center ring-8 ring-white text-slate-500">
                                <Clock className="h-4 w-4" />
                              </span>
                            </div>
                            <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                              <div>
                                <p className="text-sm font-medium text-slate-800">
                                  {act.details || act.activity_type}
                                </p>
                                <p className="text-xs text-slate-500 mt-0.5">
                                  by {act.actor_detail?.full_name || act.actor_detail?.email || 'System'}
                                </p>
                              </div>
                              <div className="text-right text-xs whitespace-nowrap text-slate-400">
                                {new Date(act.created_at).toLocaleString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (1 Col): Ticket Metadata & Admin/Agent Controls */}
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Ticket Information
            </h3>

            <div>
              <span className="text-xs text-slate-400 font-medium">Customer</span>
              <p className="text-sm font-semibold text-slate-900 mt-0.5">
                {ticket.customer_detail?.full_name || ticket.customer_detail?.email}
              </p>
              <p className="text-xs text-slate-500">{ticket.customer_detail?.email}</p>
            </div>

            <div>
              <span className="text-xs text-slate-400 font-medium">Category</span>
              <p className="text-sm font-medium text-slate-800 mt-0.5">
                {ticket.category_detail?.name || 'General Inquiry'}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400 font-medium">Assigned Support Agent</span>
              <p className="text-sm font-medium text-slate-800 mt-0.5">
                {ticket.assigned_agent_detail?.full_name || 'Unassigned'}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-100 text-xs text-slate-500 space-y-2">
              <div className="flex justify-between">
                <span>Created:</span>
                <span className="font-medium text-slate-700">
                  {new Date(ticket.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Last Updated:</span>
                <span className="font-medium text-slate-700">
                  {new Date(ticket.updated_at).toLocaleDateString()}
                </span>
              </div>
              {ticket.resolved_at && (
                <div className="flex justify-between text-emerald-700">
                  <span>Resolved At:</span>
                  <span className="font-semibold">
                    {new Date(ticket.resolved_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Controls for Staff (Agent & Admin) */}
          {isStaff && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                Staff Controls
              </h3>

              {/* Status Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Update Ticket Status
                </label>
                <select
                  value={ticket.status}
                  disabled={updatingTicket}
                  onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs bg-white font-medium focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="WAITING_FOR_CUSTOMER">Waiting Customer</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>

              {/* Priority Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Update Priority
                </label>
                <select
                  value={ticket.priority}
                  disabled={updatingTicket}
                  onChange={(e) => handlePriorityChange(e.target.value as TicketPriority)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs bg-white font-medium focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              {/* Assignee Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Assign / Reassign Agent
                </label>
                <div className="flex gap-2">
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-xs bg-white font-medium focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Unassigned</option>
                    {agents.map((ag) => (
                      <option key={ag.id} value={ag.id}>
                        {ag.full_name || ag.email} ({ag.role})
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleAssignAgent}
                    disabled={updatingTicket}
                    className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
