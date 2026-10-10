import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  Clock,
  CheckCircle,
  Flame,
  ArrowRight
} from 'lucide-react';
import { incidentsApi, servicesApi, usersApi } from '../services/api';
import type { Incident, Service, User, Severity, IncidentStatus } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';

export const IncidentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [serviceFilter, setServiceFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Create Incident Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newServiceId, setNewServiceId] = useState('');
  const [newSeverity, setNewSeverity] = useState<Severity>('HIGH');
  const [newResponderId, setNewResponderId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchIncidents = async () => {
    setIsLoading(true);
    try {
      const data = await incidentsApi.list({
        status: statusFilter ? (statusFilter as IncidentStatus) : undefined,
        severity: severityFilter ? (severityFilter as Severity) : undefined,
        service_id: serviceFilter || undefined,
        search: searchQuery.trim() || undefined,
      });
      setIncidents(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([servicesApi.list(), usersApi.list()]).then(([svcList, usrList]) => {
      setServices(svcList);
      setUsers(usrList);
      if (svcList.length > 0 && !newServiceId) {
        setNewServiceId(svcList[0].id);
      }
    });
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, severityFilter, serviceFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchIncidents();
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newServiceId) return;

    setIsSubmitting(true);
    try {
      const created = await incidentsApi.create({
        service_id: newServiceId,
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
        severity: newSeverity,
        assigned_responder_id: newResponderId || undefined,
      });
      setIsCreateModalOpen(false);
      setNewTitle('');
      setNewDescription('');
      navigate(`/incidents/${created.id}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
            Incidents Command
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Real-time incident response, lifecycle transitions, and responder assignment.
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setIsCreateModalOpen(true)}
          icon={<Plus className="w-4 h-4" />}
          data-testid="btn-create-incident"
        >
          Declare Incident
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search incident number, title, or description..."
            className="w-full pl-9 pr-4 py-2 text-xs md:text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="input-search-incidents"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-2 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-status"
          >
            <option value="">All Statuses</option>
            <option value="TRIGGERED">TRIGGERED</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="MITIGATED">MITIGATED</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-2 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-severity"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL (P1)</option>
            <option value="HIGH">HIGH (P2)</option>
            <option value="MEDIUM">MEDIUM (P3)</option>
            <option value="LOW">LOW (P4)</option>
            <option value="INFO">INFO</option>
          </select>

          {/* Service Filter */}
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="px-2.5 py-2 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-service"
          >
            <option value="">All Services</option>
            {services.map((svc) => (
              <option key={svc.id} value={svc.id}>
                {svc.name}
              </option>
            ))}
          </select>

          {(statusFilter || severityFilter || serviceFilter || searchQuery) && (
            <button
              onClick={() => {
                setStatusFilter('');
                setSeverityFilter('');
                setServiceFilter('');
                setSearchQuery('');
              }}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold px-2 py-1 cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Incidents Table / List */}
      {isLoading ? (
        <LoadingSpinner message="Fetching incidents..." />
      ) : incidents.length === 0 ? (
        <EmptyState
          title="No incidents matching criteria"
          description="All services operating normally under these filters or no incidents recorded."
          actionText="Declare New Incident"
          onAction={() => setIsCreateModalOpen(true)}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse" data-testid="incidents-table">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/70">
                  <th className="py-3 px-4 font-semibold">Incident</th>
                  <th className="py-3 px-3 font-semibold">Severity</th>
                  <th className="py-3 px-3 font-semibold">Status</th>
                  <th className="py-3 px-3 font-semibold">Service</th>
                  <th className="py-3 px-3 font-semibold">Assigned Responder</th>
                  <th className="py-3 px-3 font-semibold">SLA / Deadline</th>
                  <th className="py-3 px-3 font-semibold">Created</th>
                  <th className="py-3 px-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {incidents.map((inc) => {
                  const isDeadlineBreached = inc.ack_deadline && new Date(inc.ack_deadline) < new Date() && inc.status === 'TRIGGERED';
                  return (
                    <tr
                      key={inc.id}
                      onClick={() => navigate(`/incidents/${inc.id}`)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                      data-testid={`incident-row-${inc.incident_number}`}
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-indigo-600 group-hover:underline">
                            #{inc.incident_number}
                          </span>
                          <span className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {inc.title}
                          </span>
                          {inc.alert_count > 1 && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200">
                              {inc.alert_count} alerts
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-3.5 px-3">
                        <Badge value={inc.severity} />
                      </td>

                      <td className="py-3.5 px-3">
                        <Badge value={inc.status} />
                      </td>

                      <td className="py-3.5 px-3 font-medium text-slate-700">
                        {inc.service_name}
                      </td>

                      <td className="py-3.5 px-3 text-slate-600">
                        {inc.assigned_responder_name || (
                          <span className="italic text-slate-400">Unassigned</span>
                        )}
                      </td>

                      <td className="py-3.5 px-3 font-mono text-[11px]">
                        {inc.status === 'TRIGGERED' && inc.ack_deadline ? (
                          isDeadlineBreached ? (
                            <span className="text-red-600 font-semibold flex items-center gap-1">
                              <Flame className="w-3 h-3" /> SLA BREACH
                            </span>
                          ) : (
                            <span className="text-amber-700 font-medium flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Due {new Date(inc.ack_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )
                        ) : inc.status === 'RESOLVED' ? (
                          <span className="text-emerald-600 font-medium flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> Met
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>

                      <td className="py-3.5 px-3 text-slate-400 font-mono text-[11px]">
                        {new Date(inc.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                        {new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>

                      <td className="py-3.5 px-3 text-right">
                        <span className="text-xs font-semibold text-indigo-600 group-hover:translate-x-1 inline-flex items-center gap-1 transition-transform">
                          Details <ArrowRight className="w-3 h-3" />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Declare Incident Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Declare New Incident"
        description="Trigger an active incident for a monitored service. Automatically kicks off on-call escalation."
      >
        <form onSubmit={handleCreateIncident} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Affected Service *
            </label>
            <select
              required
              value={newServiceId}
              onChange={(e) => setNewServiceId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-new-incident-service"
            >
              {services.map((svc) => (
                <option key={svc.id} value={svc.id}>
                  {svc.name} ({svc.environment})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Incident Title / Summary *
            </label>
            <input
              type="text"
              required
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Ingestion pipeline backlog exceeding 100k messages"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-new-incident-title"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Severity
              </label>
              <select
                value={newSeverity}
                onChange={(e) => setNewSeverity(e.target.value as Severity)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                data-testid="input-new-incident-severity"
              >
                <option value="CRITICAL">CRITICAL (P1)</option>
                <option value="HIGH">HIGH (P2)</option>
                <option value="MEDIUM">MEDIUM (P3)</option>
                <option value="LOW">LOW (P4)</option>
                <option value="INFO">INFO</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Initial Responder (Optional)
              </label>
              <select
                value={newResponderId}
                onChange={(e) => setNewResponderId(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                data-testid="input-new-incident-responder"
              >
                <option value="">Auto-assign via Escalation Policy</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.role})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Description / Diagnostic Notes
            </label>
            <textarea
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              rows={3}
              placeholder="Provide symptoms, suspected root causes, customer impact..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-new-incident-desc"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              data-testid="btn-submit-new-incident"
            >
              Declare Incident
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
