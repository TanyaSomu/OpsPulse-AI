import React, { useState, useEffect } from 'react';
import { Filter } from 'lucide-react';
import { auditApi } from '../services/api';
import type { AuditEvent } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';

export const AuditPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [targetFilter, setTargetFilter] = useState('');

  const fetchAuditEvents = async () => {
    setIsLoading(true);
    try {
      const data = await auditApi.list({
        target_type: targetFilter || undefined,
      });
      setEvents(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
  }, [targetFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
            System Audit Trail
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Immutable chronological operational audit log across all backend actions and lifecycle state changes.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Filter Target:</span>
          <select
            value={targetFilter}
            onChange={(e) => setTargetFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="filter-audit-target"
          >
            <option value="">All Targets</option>
            <option value="INCIDENT">INCIDENT</option>
            <option value="ALERT">ALERT</option>
            <option value="SERVICE">SERVICE</option>
            <option value="POLICY">POLICY</option>
            <option value="USER">USER</option>
          </select>

          {targetFilter && (
            <button
              onClick={() => setTargetFilter('')}
              className="text-xs text-indigo-600 font-semibold px-2 py-1 cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>
        <span className="text-xs text-slate-400 font-mono">Immutable Log</span>
      </div>

      {/* Audit Log Table */}
      {isLoading ? (
        <LoadingSpinner message="Querying audit records..." />
      ) : events.length === 0 ? (
        <EmptyState
          title="No audit events found"
          description="Operational actions performed in OpsPulse AI will be permanently recorded here."
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse" data-testid="audit-table">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/70">
                  <th className="py-3 px-4 font-semibold">Timestamp</th>
                  <th className="py-3 px-3 font-semibold">Event Type</th>
                  <th className="py-3 px-3 font-semibold">Target</th>
                  <th className="py-3 px-3 font-semibold">Actor</th>
                  <th className="py-3 px-4 font-semibold">Operational Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(evt.created_at).toLocaleString()}
                    </td>

                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">
                        {evt.event_type}
                      </span>
                    </td>

                    <td className="py-3 px-3 font-semibold text-slate-700">
                      {evt.target_type}
                    </td>

                    <td className="py-3 px-3 text-slate-600 font-sans">
                      {evt.actor_email}
                    </td>

                    <td className="py-3 px-4 font-sans text-xs text-slate-800">
                      {evt.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
