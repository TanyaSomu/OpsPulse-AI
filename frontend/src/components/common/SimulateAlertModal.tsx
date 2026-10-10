import React, { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { servicesApi, alertsApi } from '../../services/api';
import type { Service, Severity } from '../../types';

interface SimulateAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const SimulateAlertModal: React.FC<SimulateAlertModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState<Severity>('HIGH');
  const [source, setSource] = useState('Datadog');
  const [isLoading, setIsLoading] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      servicesApi.list().then((list) => {
        setServices(list);
        if (list.length > 0 && !selectedServiceId) {
          setSelectedServiceId(list[0].id);
        }
      });
      setResultMessage(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsLoading(true);
    try {
      const res = await alertsApi.simulateWebhook({
        service_id: selectedServiceId,
        title: title.trim(),
        description: description.trim() || undefined,
        severity,
        source,
        metadata: { simulated_by: 'OpsPulse UI Test Console' }
      });

      if (res.is_new_incident) {
        setResultMessage(`Created new Incident #${res.incident_number}`);
      } else {
        setResultMessage(`Correlated & deduplicated into Incident #${res.incident_number}`);
      }

      if (onSuccess) onSuccess();
      setTimeout(() => {
        onClose();
        setTitle('');
        setDescription('');
      }, 1500);
    } catch {
      setResultMessage('Failed to send webhook alert');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Simulate Webhook Alert"
      description="Inject an alert payload via webhook to test deduplication, correlation, and SLA escalation."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {resultMessage && (
          <div className="p-3 text-xs font-semibold text-emerald-800 bg-emerald-50 rounded-lg border border-emerald-200">
            {resultMessage}
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Target Service
          </label>
          <select
            value={selectedServiceId}
            onChange={(e) => setSelectedServiceId(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="input-alert-service"
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
            Alert Title / Problem Summary *
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Memory utilization exceeded 92% on pod worker-3"
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="input-alert-title"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Severity
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-alert-severity"
            >
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="INFO">INFO</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Monitoring Source
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-alert-source"
            >
              <option value="Datadog">Datadog</option>
              <option value="Prometheus">Prometheus</option>
              <option value="Grafana">Grafana</option>
              <option value="CloudWatch">AWS CloudWatch</option>
              <option value="PagerDuty Webhook">PagerDuty Webhook</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Description / Diagnostic Context
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            placeholder="Metric values, stack trace or error log snippet"
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="input-alert-desc"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            data-testid="btn-submit-simulate-alert"
          >
            Dispatch Alert
          </Button>
        </div>
      </form>
    </Modal>
  );
};
