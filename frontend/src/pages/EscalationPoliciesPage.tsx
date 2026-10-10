import React, { useState, useEffect } from 'react';
import { Plus, Clock } from 'lucide-react';
import { escalationApi, usersApi } from '../services/api';
import type { EscalationPolicy, User } from '../types';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { useAuth } from '../context/AuthContext';

export const EscalationPoliciesPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const [policies, setPolicies] = useState<EscalationPolicy[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // New Policy Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [timeoutMinutes, setTimeoutMinutes] = useState(5);
  const [level1UserId, setLevel1UserId] = useState('');
  const [level2UserId, setLevel2UserId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPolicies = async () => {
    setIsLoading(true);
    try {
      const [polData, usrData] = await Promise.all([
        escalationApi.list(),
        usersApi.list(),
      ]);
      setPolicies(polData);
      setUsers(usrData);
      if (usrData.length > 0 && !level1UserId) {
        setLevel1UserId(usrData[0].id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !level1UserId) return;

    setIsSubmitting(true);
    try {
      const rules = [{ level_number: 1, user_id: level1UserId }];
      if (level2UserId && level2UserId !== level1UserId) {
        rules.push({ level_number: 2, user_id: level2UserId });
      }

      await escalationApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        ack_timeout_seconds: timeoutMinutes * 60,
        rules,
      });

      setIsModalOpen(false);
      setName('');
      setDescription('');
      await fetchPolicies();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
            Escalation Policies
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Configure automated on-call routing tiers and SLA acknowledgement deadlines.
          </p>
        </div>
        {isAdmin && (
          <Button
            variant="primary"
            onClick={() => setIsModalOpen(true)}
            icon={<Plus className="w-4 h-4" />}
            data-testid="btn-add-escalation-policy"
          >
            New Policy
          </Button>
        )}
      </div>

      {isLoading ? (
        <LoadingSpinner message="Loading escalation policies..." />
      ) : policies.length === 0 ? (
        <EmptyState
          title="No escalation policies defined"
          description="Create escalation tiers to automatically notify responders when incidents breach acknowledgement deadlines."
          actionText="Create Policy"
          onAction={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {policies.map((pol) => (
            <div
              key={pol.id}
              className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between"
              data-testid={`policy-card-${pol.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{pol.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="flex items-center gap-1 text-xs font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                        <Clock className="w-3 h-3" /> {pol.ack_timeout_seconds / 60}m Ack Timeout
                      </span>
                      {pol.is_active ? (
                        <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                          INACTIVE
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {pol.description && (
                  <p className="text-xs text-slate-600 mt-2 mb-4">
                    {pol.description}
                  </p>
                )}

                {/* Escalation Ladder */}
                <div className="space-y-2 mt-4 pt-4 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Escalation Tiers
                  </span>
                  {pol.rules.map((rule, idx) => (
                    <div
                      key={rule.id}
                      className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-mono font-bold flex items-center justify-center text-[11px]">
                          {rule.level_number}
                        </span>
                        <div>
                          <p className="font-semibold text-slate-800">{rule.user_name || 'Assigned User'}</p>
                          <p className="text-[10px] text-slate-500">{rule.user_email}</p>
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {idx === 0 ? 'Initial Page' : `+${pol.ack_timeout_seconds / 60}m Escalation`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: New Policy */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Escalation Policy"
        description="Define an ordered response chain with configurable SLA deadlines."
      >
        <form onSubmit={handleCreatePolicy} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Policy Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Critical Infrastructure 2-Min Escalation"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-policy-name"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Acknowledgement Timeout (Minutes) *
            </label>
            <input
              type="number"
              min={1}
              max={60}
              required
              value={timeoutMinutes}
              onChange={(e) => setTimeoutMinutes(parseInt(e.target.value) || 5)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-policy-timeout"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Tier 1 Responder (First Page) *
            </label>
            <select
              value={level1UserId}
              onChange={(e) => setLevel1UserId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-policy-tier1"
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Tier 2 Responder (Escalation target on SLA breach)
            </label>
            <select
              value={level2UserId}
              onChange={(e) => setLevel2UserId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-policy-tier2"
            >
              <option value="">None (Single level)</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Policy Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="e.g. Standard on-call schedule for production core engineering"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-policy-desc"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              data-testid="btn-submit-policy"
            >
              Save Policy
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
