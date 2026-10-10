import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit2 } from 'lucide-react';
import { servicesApi, escalationApi } from '../services/api';
import type { Service, EscalationPolicy, ServiceHealth } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { useAuth } from '../context/AuthContext';

export const ServicesPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  const [services, setServices] = useState<Service[]>([]);
  const [policies, setPolicies] = useState<EscalationPolicy[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Register Modal state
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ownerTeam, setOwnerTeam] = useState('Core Engineering');
  const [environment, setEnvironment] = useState('production');
  const [policyId, setPolicyId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Edit Modal state
  const [editingService, setEditingService] = useState<Service | null>(null);

  const fetchServices = async () => {
    setIsLoading(true);
    try {
      const [svcData, polData] = await Promise.all([
        servicesApi.list(),
        escalationApi.list()
      ]);
      setServices(svcData);
      setPolicies(polData);
      if (polData.length > 0 && !policyId) {
        setPolicyId(polData[0].id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const handleRegisterService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await servicesApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        owner_team: ownerTeam.trim(),
        environment,
        health_status: 'HEALTHY',
        escalation_policy_id: policyId || undefined
      });
      setIsRegisterModalOpen(false);
      setName('');
      setDescription('');
      await fetchServices();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingService) return;

    setIsSubmitting(true);
    try {
      await servicesApi.update(editingService.id, {
        name: editingService.name,
        description: editingService.description,
        owner_team: editingService.owner_team,
        environment: editingService.environment,
        health_status: editingService.health_status,
        escalation_policy_id: editingService.escalation_policy_id || undefined,
        is_active: editingService.is_active,
      });
      setEditingService(null);
      await fetchServices();
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
            Services Catalog
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Manage monitored microservices, ownership routing, and escalation mapping.
          </p>
        </div>
        {isAdmin && (
          <Button
            variant="primary"
            onClick={() => setIsRegisterModalOpen(true)}
            icon={<Plus className="w-4 h-4" />}
            data-testid="btn-register-service"
          >
            Register Service
          </Button>
        )}
      </div>

      {/* Services Grid */}
      {isLoading ? (
        <LoadingSpinner message="Fetching monitored services..." />
      ) : services.length === 0 ? (
        <EmptyState
          title="No registered services"
          description="Register services to begin ingesting alerts and tracking incident reliability."
          actionText="Register Service"
          onAction={() => setIsRegisterModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="services-grid">
          {services.map((svc) => (
            <div
              key={svc.id}
              className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
              data-testid={`service-card-${svc.slug}`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="overflow-hidden">
                    <h3 className="text-base font-bold text-slate-900 truncate">{svc.name}</h3>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">{svc.environment} • {svc.owner_team}</p>
                  </div>
                  <Badge value={svc.health_status} />
                </div>

                {svc.description && (
                  <p className="text-xs text-slate-600 line-clamp-2 mt-2">
                    {svc.description}
                  </p>
                )}

                <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs text-slate-500">
                  <div className="flex justify-between">
                    <span>Active Incidents:</span>
                    <span className={svc.active_incident_count > 0 ? 'font-bold text-red-600' : 'font-medium text-slate-800'}>
                      {svc.active_incident_count}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Escalation Policy:</span>
                    <span className="font-medium text-slate-800 truncate max-w-[150px]">
                      {svc.escalation_policy_name || 'Standard SLA'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => navigate(`/incidents?service_id=${svc.id}`)}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
                >
                  View Incidents ({svc.active_incident_count})
                </button>

                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setEditingService({ ...svc })}
                    icon={<Edit2 className="w-3.5 h-3.5" />}
                    data-testid={`btn-edit-service-${svc.slug}`}
                  >
                    Edit
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Register Modal */}
      <Modal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        title="Register Monitored Service"
        description="Add a service or microservice to enable alert ingestion and automatic incident assignment."
      >
        <form onSubmit={handleRegisterService} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Service Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Checkout Cart Service"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-register-service-name"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Owner Team
              </label>
              <input
                type="text"
                required
                value={ownerTeam}
                onChange={(e) => setOwnerTeam(e.target.value)}
                placeholder="e.g. Core Commerce"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                data-testid="input-register-service-team"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Environment
              </label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                data-testid="select-register-service-env"
              >
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="development">Development</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Escalation Policy
            </label>
            <select
              value={policyId}
              onChange={(e) => setPolicyId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-register-service-policy"
            >
              <option value="">Default Organization Policy</option>
              {policies.map((pol) => (
                <option key={pol.id} value={pol.id}>
                  {pol.name} ({pol.ack_timeout_seconds / 60}m timeout)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Description / Responsibilities
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Primary functions and downstream dependencies"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-register-service-desc"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsRegisterModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              data-testid="btn-submit-register-service"
            >
              Register Service
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      {editingService && (
        <Modal
          isOpen={true}
          onClose={() => setEditingService(null)}
          title={`Edit Service: ${editingService.name}`}
        >
          <form onSubmit={handleUpdateService} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Name</label>
              <input
                type="text"
                required
                value={editingService.name}
                onChange={(e) => setEditingService({ ...editingService, name: e.target.value })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Owner Team</label>
                <input
                  type="text"
                  required
                  value={editingService.owner_team}
                  onChange={(e) => setEditingService({ ...editingService, owner_team: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Health Status</label>
                <select
                  value={editingService.health_status}
                  onChange={(e) => setEditingService({ ...editingService, health_status: e.target.value as ServiceHealth })}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="HEALTHY">HEALTHY</option>
                  <option value="DEGRADED">DEGRADED</option>
                  <option value="FAILING">FAILING</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Escalation Policy</label>
              <select
                value={editingService.escalation_policy_id || ''}
                onChange={(e) => setEditingService({ ...editingService, escalation_policy_id: e.target.value || undefined })}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Default Organization Policy</option>
                {policies.map((pol) => (
                  <option key={pol.id} value={pol.id}>
                    {pol.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button type="button" variant="outline" onClick={() => setEditingService(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
