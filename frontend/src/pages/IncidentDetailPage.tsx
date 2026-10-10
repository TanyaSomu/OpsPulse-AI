import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  UserCheck,
  Send,
  Activity,
  History,
  BellRing,
  RotateCcw,
  Check,
  ShieldAlert
} from 'lucide-react';
import { incidentsApi, usersApi } from '../services/api';
import type { IncidentDetail, User, Severity } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Note/Update form state
  const [noteMessage, setNoteMessage] = useState('');
  const [isPostingNote, setIsPostingNote] = useState(false);

  // Action modals
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');

  const [isMitigateModalOpen, setIsMitigateModalOpen] = useState(false);
  const [mitigateNote, setMitigateNote] = useState('');

  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolveNote, setResolveNote] = useState('');

  const [isReopenModalOpen, setIsReopenModalOpen] = useState(false);
  const [reopenNote, setReopenNote] = useState('');

  const [isSeverityModalOpen, setIsSeverityModalOpen] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState<Severity>('HIGH');

  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'alerts' | 'updates'>('timeline');

  const fetchIncidentData = async () => {
    if (!id) return;
    try {
      const data = await incidentsApi.get(id);
      setIncident(data);
      setSelectedSeverity(data.severity);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Incident not found.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidentData();
    usersApi.list().then(setUsers);
  }, [id]);

  const handleAcknowledge = async () => {
    if (!incident) return;
    setActionLoading(true);
    try {
      await incidentsApi.acknowledge(incident.id);
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident || !selectedUserId) return;
    setActionLoading(true);
    try {
      await incidentsApi.assign(incident.id, selectedUserId);
      setIsAssignModalOpen(false);
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleMitigate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident) return;
    setActionLoading(true);
    try {
      await incidentsApi.mitigate(incident.id, mitigateNote.trim() || undefined);
      setIsMitigateModalOpen(false);
      setMitigateNote('');
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident) return;
    setActionLoading(true);
    try {
      await incidentsApi.resolve(incident.id, resolveNote.trim() || undefined);
      setIsResolveModalOpen(false);
      setResolveNote('');
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleReopen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident) return;
    setActionLoading(true);
    try {
      await incidentsApi.reopen(incident.id, reopenNote.trim() || undefined);
      setIsReopenModalOpen(false);
      setReopenNote('');
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleSeverityChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident) return;
    setActionLoading(true);
    try {
      await incidentsApi.update(incident.id, { severity: selectedSeverity });
      setIsSeverityModalOpen(false);
      await fetchIncidentData();
    } finally {
      setActionLoading(false);
    }
  };

  const handlePostNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!incident || !noteMessage.trim()) return;
    setIsPostingNote(true);
    try {
      await incidentsApi.postUpdate(incident.id, noteMessage.trim());
      setNoteMessage('');
      await fetchIncidentData();
      setActiveTab('updates');
    } finally {
      setIsPostingNote(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading incident timeline..." />;
  }

  if (error || !incident) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <p className="text-base font-semibold text-slate-800">{error || 'Incident not found'}</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/incidents')} className="mt-4">
          Back to Incidents
        </Button>
      </div>
    );
  }

  const isTriggered = incident.status === 'TRIGGERED';
  const isAcknowledged = incident.status === 'ACKNOWLEDGED';
  const isResolved = incident.status === 'RESOLVED';

  return (
    <div className="space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <button
          onClick={() => navigate('/incidents')}
          className="flex items-center gap-1 hover:text-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents
        </button>
        <span>/</span>
        <span className="font-mono font-semibold text-slate-900">INC-#{incident.incident_number}</span>
      </div>

      {/* Incident Header & Command Bar */}
      <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="font-mono text-base font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                #{incident.incident_number}
              </span>
              <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
                {incident.title}
              </h1>
              <Badge value={incident.severity} size="md" />
              <Badge value={incident.status} size="md" />
            </div>
            {incident.description && (
              <p className="text-sm text-slate-600 max-w-3xl pt-1">
                {incident.description}
              </p>
            )}
          </div>

          {/* Action Bar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {/* Acknowledge (when TRIGGERED) */}
            {isTriggered && (
              <Button
                variant="primary"
                onClick={handleAcknowledge}
                isLoading={actionLoading}
                icon={<CheckCircle className="w-4 h-4" />}
                data-testid="btn-action-acknowledge"
              >
                Acknowledge SLA
              </Button>
            )}

            {/* Mitigate (when TRIGGERED or ACKNOWLEDGED) */}
            {(isTriggered || isAcknowledged) && (
              <Button
                variant="outline"
                onClick={() => setIsMitigateModalOpen(true)}
                icon={<ShieldAlert className="w-4 h-4 text-indigo-600" />}
                data-testid="btn-action-mitigate"
              >
                Mitigate
              </Button>
            )}

            {/* Resolve (when not yet resolved) */}
            {!isResolved && (
              <Button
                variant="secondary"
                onClick={() => setIsResolveModalOpen(true)}
                icon={<Check className="w-4 h-4 text-emerald-400" />}
                data-testid="btn-action-resolve"
              >
                Resolve
              </Button>
            )}

            {/* Reopen (when resolved) */}
            {isResolved && (
              <Button
                variant="outline"
                onClick={() => setIsReopenModalOpen(true)}
                icon={<RotateCcw className="w-4 h-4 text-amber-600" />}
                data-testid="btn-action-reopen"
              >
                Reopen Incident
              </Button>
            )}

            {/* Reassign */}
            <Button
              variant="outline"
              onClick={() => {
                setSelectedUserId(incident.assigned_responder_id || '');
                setIsAssignModalOpen(true);
              }}
              icon={<UserCheck className="w-4 h-4 text-slate-500" />}
              data-testid="btn-action-assign"
            >
              Assign
            </Button>

            {/* Change Severity */}
            <Button
              variant="ghost"
              onClick={() => setIsSeverityModalOpen(true)}
              data-testid="btn-action-change-severity"
            >
              Change Severity
            </Button>
          </div>
        </div>

        {/* Operational Context Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-100 text-xs">
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Affected Service</span>
            <p className="font-semibold text-slate-800 mt-0.5 truncate">{incident.service_name}</p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Assigned Responder</span>
            <p className="font-semibold text-slate-800 mt-0.5 truncate">
              {incident.assigned_responder_name || <span className="italic text-slate-400">Unassigned</span>}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Escalation Policy</span>
            <p className="font-semibold text-slate-800 mt-0.5 truncate">
              {incident.escalation_policy_name || 'Standard SLA'}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Escalation Tier</span>
            <p className="font-semibold text-slate-800 mt-0.5">
              Level {incident.current_escalation_level}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">SLA Ack Deadline</span>
            <p className="font-semibold text-slate-800 mt-0.5 font-mono">
              {incident.ack_deadline ? (
                new Date(incident.ack_deadline) < new Date() && isTriggered ? (
                  <span className="text-red-600">BREACHED</span>
                ) : (
                  new Date(incident.ack_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                )
              ) : incident.acknowledged_at ? (
                <span className="text-emerald-600">Acknowledged</span>
              ) : (
                '—'
              )}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Correlated Alerts</span>
            <p className="font-semibold text-slate-800 mt-0.5 font-mono">
              {incident.alert_count} alert(s)
            </p>
          </div>
        </div>
      </div>

      {/* Main Tabs Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-200 bg-slate-50/60 px-6">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`py-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              activeTab === 'timeline'
                ? 'border-indigo-600 text-indigo-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
            data-testid="tab-timeline"
          >
            <History className="w-4 h-4" />
            Audit Timeline ({incident.events.length})
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              activeTab === 'alerts'
                ? 'border-indigo-600 text-indigo-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
            data-testid="tab-alerts"
          >
            <BellRing className="w-4 h-4" />
            Correlated Alerts ({incident.alerts.length})
          </button>

          <button
            onClick={() => setActiveTab('updates')}
            className={`py-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              activeTab === 'updates'
                ? 'border-indigo-600 text-indigo-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
            data-testid="tab-updates"
          >
            <Activity className="w-4 h-4" />
            Investigation Notes ({incident.updates.length})
          </button>
        </div>

        {/* Tab Content Panels */}
        <div className="p-6">
          {/* TAB 1: TIMELINE */}
          {activeTab === 'timeline' && (
            <div className="space-y-6">
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {incident.events.map((evt) => (
                  <div key={evt.id} className="relative group">
                    <div className="absolute -left-6 top-1 w-4 h-4 rounded-full border-2 border-white bg-indigo-600 ring-2 ring-indigo-100" />
                    <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-500">
                        <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                          <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 text-[10px] font-mono">
                            {evt.event_type}
                          </span>
                          {evt.actor_name}
                        </span>
                        <span className="font-mono text-[11px] text-slate-400">
                          {new Date(evt.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-slate-700 pt-0.5">{evt.message}</p>
                      {evt.metadata_json && Object.keys(evt.metadata_json).length > 0 && (
                        <pre className="mt-1.5 p-2 rounded bg-slate-900 text-slate-200 text-[10px] font-mono overflow-x-auto">
                          {JSON.stringify(evt.metadata_json, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: CORRELATED ALERTS */}
          {activeTab === 'alerts' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/70">
                    <th className="py-2.5 px-3 font-semibold">Title</th>
                    <th className="py-2.5 px-3 font-semibold">Source</th>
                    <th className="py-2.5 px-3 font-semibold">Severity</th>
                    <th className="py-2.5 px-3 font-semibold">Status</th>
                    <th className="py-2.5 px-3 font-semibold">Fingerprint</th>
                    <th className="py-2.5 px-3 font-semibold">Received</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {incident.alerts.map((alt) => (
                    <tr key={alt.id} className="hover:bg-slate-50/80">
                      <td className="py-3 px-3 font-semibold text-slate-800">
                        {alt.title}
                        {alt.description && (
                          <p className="font-normal text-slate-500 text-[11px] mt-0.5">{alt.description}</p>
                        )}
                      </td>
                      <td className="py-3 px-3 font-medium text-slate-600">{alt.source}</td>
                      <td className="py-3 px-3">
                        <Badge value={alt.severity} />
                      </td>
                      <td className="py-3 px-3">
                        <Badge value={alt.status} />
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">
                        {alt.fingerprint.slice(0, 12)}...
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">
                        {new Date(alt.received_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: INVESTIGATION UPDATES / COMMENTS */}
          {activeTab === 'updates' && (
            <div className="space-y-6">
              {/* Post Note Form */}
              <form onSubmit={handlePostNote} className="space-y-3 p-4 rounded-xl border border-slate-200 bg-slate-50">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Add Investigation Note or Action Item
                </label>
                <textarea
                  required
                  rows={2}
                  value={noteMessage}
                  onChange={(e) => setNoteMessage(e.target.value)}
                  placeholder="e.g. Scaled downstream deployment from 2 to 6 replicas. Investigating connection timeouts..."
                  className="w-full px-3 py-2 text-xs md:text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  data-testid="input-investigation-note"
                />
                <div className="flex justify-end">
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    isLoading={isPostingNote}
                    icon={<Send className="w-3.5 h-3.5" />}
                    data-testid="btn-submit-note"
                  >
                    Post Update
                  </Button>
                </div>
              </form>

              {/* Notes stream */}
              <div className="space-y-3">
                {incident.updates.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-6">
                    No investigation updates posted yet.
                  </p>
                ) : (
                  incident.updates.map((upd) => (
                    <div key={upd.id} className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-1">
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span className="font-semibold text-slate-800">{upd.user_name}</span>
                        <span className="font-mono text-[11px] text-slate-400">
                          {new Date(upd.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-xs md:text-sm text-slate-700 whitespace-pre-wrap">{upd.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal: Assign Responder */}
      <Modal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        title="Assign Incident Responder"
        description="Select an engineering responder to take command of this incident."
      >
        <form onSubmit={handleAssign} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Select Responder
            </label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-assign-user"
            >
              <option value="">Select a responder...</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.role}) - {u.email}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsAssignModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={!selectedUserId}
              isLoading={actionLoading}
              data-testid="btn-submit-assign"
            >
              Confirm Assignment
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Mitigate */}
      <Modal
        isOpen={isMitigateModalOpen}
        onClose={() => setIsMitigateModalOpen(false)}
        title="Mark Incident as Mitigated"
        description="Verify impact has subsided while root cause investigation continues."
      >
        <form onSubmit={handleMitigate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Mitigation Note
            </label>
            <textarea
              value={mitigateNote}
              onChange={(e) => setMitigateNote(e.target.value)}
              rows={2}
              placeholder="e.g. Traffic rerouted to secondary datacenter. Error rate back under 0.1%."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-mitigate-note"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsMitigateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={actionLoading}
              data-testid="btn-submit-mitigate"
            >
              Confirm Mitigated
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Resolve */}
      <Modal
        isOpen={isResolveModalOpen}
        onClose={() => setIsResolveModalOpen(false)}
        title="Resolve Incident"
        description="Close this incident. If all active issues on this service are resolved, service health will be set to Healthy."
      >
        <form onSubmit={handleResolve} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Resolution Summary
            </label>
            <textarea
              value={resolveNote}
              onChange={(e) => setResolveNote(e.target.value)}
              rows={2}
              placeholder="e.g. Deployed hotfix v2.4.1 fixing memory leak in session parser."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-resolve-note"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsResolveModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="secondary"
              isLoading={actionLoading}
              data-testid="btn-submit-resolve"
            >
              Confirm Resolved
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Reopen */}
      <Modal
        isOpen={isReopenModalOpen}
        onClose={() => setIsReopenModalOpen(false)}
        title="Reopen Incident"
        description="Re-trigger an active incident state and resume on-call SLA countdown."
      >
        <form onSubmit={handleReopen} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Reason for Reopening
            </label>
            <textarea
              required
              value={reopenNote}
              onChange={(e) => setReopenNote(e.target.value)}
              rows={2}
              placeholder="e.g. Symptoms recurred after traffic spike."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-reopen-note"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsReopenModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="danger"
              isLoading={actionLoading}
              data-testid="btn-submit-reopen"
            >
              Reopen Incident
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Change Severity */}
      <Modal
        isOpen={isSeverityModalOpen}
        onClose={() => setIsSeverityModalOpen(false)}
        title="Update Incident Severity"
        description="Adjust severity classification based on evaluated customer or operational impact."
      >
        <form onSubmit={handleSeverityChange} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Severity Level
            </label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value as Severity)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-change-severity"
            >
              <option value="CRITICAL">CRITICAL (P1)</option>
              <option value="HIGH">HIGH (P2)</option>
              <option value="MEDIUM">MEDIUM (P3)</option>
              <option value="LOW">LOW (P4)</option>
              <option value="INFO">INFO</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsSeverityModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={actionLoading}
              data-testid="btn-submit-change-severity"
            >
              Update Severity
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
