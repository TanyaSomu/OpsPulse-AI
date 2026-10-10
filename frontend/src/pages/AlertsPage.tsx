import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Filter, Code, ArrowUpRight, Plus } from 'lucide-react';
import { alertsApi, servicesApi } from '../services/api';
import type { Alert, Service, Severity } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { SimulateAlertModal } from '../components/common/SimulateAlertModal';

export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [serviceFilter, setServiceFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Modals
  const [selectedAlertForPayload, setSelectedAlertForPayload] = useState<Alert | null>(null);
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState(false);

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await alertsApi.list({
        service_id: serviceFilter || undefined,
        severity: severityFilter ? (severityFilter as Severity) : undefined,
      });
      setAlerts(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    servicesApi.list().then(setServices);
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [serviceFilter, severityFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
            Incoming Webhook Alerts
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Real-time telemetry stream, automated fingerprinting, and deduplication audit log.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => setIsSimulateModalOpen(true)}
          icon={<Plus className="w-4 h-4 text-indigo-400" />}
          data-testid="btn-alerts-simulate"
        >
          Simulate Alert Webhook
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Filters:</span>
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-alerts-service"
          >
            <option value="">All Services</option>
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-alerts-severity"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
            <option value="INFO">INFO</option>
          </select>

          {(serviceFilter || severityFilter) && (
            <button
              onClick={() => {
                setServiceFilter('');
                setSeverityFilter('');
              }}
              className="text-xs text-indigo-600 font-semibold px-2 py-1 cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Endpoint: <span className="text-slate-600 font-semibold">POST /api/v1/alerts/webhook</span>
        </div>
      </div>

      {/* Alerts Table */}
      {isLoading ? (
        <LoadingSpinner message="Fetching alert log..." />
      ) : alerts.length === 0 ? (
        <EmptyState
          title="No alerts logged"
          description="Webhook alerts dispatched to /api/v1/alerts/webhook will appear here in real-time."
          actionText="Dispatch Test Alert"
          onAction={() => setIsSimulateModalOpen(true)}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse" data-testid="alerts-table">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/70">
                  <th className="py-3 px-4 font-semibold">Alert Summary</th>
                  <th className="py-3 px-3 font-semibold">Source</th>
                  <th className="py-3 px-3 font-semibold">Affected Service</th>
                  <th className="py-3 px-3 font-semibold">Severity</th>
                  <th className="py-3 px-3 font-semibold">Ingestion Status</th>
                  <th className="py-3 px-3 font-semibold">Fingerprint</th>
                  <th className="py-3 px-3 font-semibold">Received</th>
                  <th className="py-3 px-3 text-right font-semibold">Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {alerts.map((alt) => (
                  <tr key={alt.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{alt.title}</div>
                      {alt.description && (
                        <p className="text-[11px] text-slate-500 truncate max-w-sm mt-0.5">
                          {alt.description}
                        </p>
                      )}
                    </td>

                    <td className="py-3 px-3 font-medium text-slate-700">
                      {alt.source}
                    </td>

                    <td className="py-3 px-3 text-slate-800 font-medium">
                      {alt.service_name}
                    </td>

                    <td className="py-3 px-3">
                      <Badge value={alt.severity} />
                    </td>

                    <td className="py-3 px-3">
                      <Badge value={alt.status} />
                    </td>

                    <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">
                      {alt.fingerprint.slice(0, 10)}...
                    </td>

                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(alt.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>

                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedAlertForPayload(alt)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
                        data-testid={`btn-inspect-payload-${alt.id}`}
                      >
                        <Code className="w-3.5 h-3.5" /> Payload
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Inspect Payload Modal */}
      {selectedAlertForPayload && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedAlertForPayload(null)}
          title={`Alert Payload: ${selectedAlertForPayload.title}`}
          maxWidth="lg"
        >
          <div className="space-y-3">
            <div className="p-3 bg-slate-900 rounded-lg text-slate-100 text-xs font-mono overflow-x-auto max-h-80">
              <pre>{JSON.stringify(selectedAlertForPayload.payload || {}, null, 2)}</pre>
            </div>
            {selectedAlertForPayload.incident_id && (
              <div className="pt-2 flex justify-between items-center text-xs">
                <span className="text-slate-500">Associated Incident:</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/incidents/${selectedAlertForPayload.incident_id}`)}
                >
                  View Incident Record <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Webhook Simulation Modal */}
      <SimulateAlertModal
        isOpen={isSimulateModalOpen}
        onClose={() => setIsSimulateModalOpen(false)}
        onSuccess={fetchAlerts}
      />
    </div>
  );
};
