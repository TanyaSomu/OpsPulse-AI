import React, { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { usersApi } from '../services/api';
import type { User, UserRole } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useAuth } from '../context/AuthContext';

export const UsersPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Add User Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('RESPONDER');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await usersApi.list();
      setUsers(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !fullName.trim() || !password) return;

    setIsSubmitting(true);
    try {
      await usersApi.create({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role,
      });
      setIsModalOpen(false);
      setFullName('');
      setEmail('');
      setPassword('');
      await fetchUsers();
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
            Responders & Team Access
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Manage engineering on-call responders and role-based permissions (RBAC).
          </p>
        </div>
        {isAdmin && (
          <Button
            variant="primary"
            onClick={() => setIsModalOpen(true)}
            icon={<Plus className="w-4 h-4" />}
            data-testid="btn-add-user"
          >
            Add Team Member
          </Button>
        )}
      </div>

      {isLoading ? (
        <LoadingSpinner message="Fetching team responders..." />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse" data-testid="users-table">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/70">
                  <th className="py-3 px-4 font-semibold">Member Name</th>
                  <th className="py-3 px-3 font-semibold">Work Email</th>
                  <th className="py-3 px-3 font-semibold">Access Role</th>
                  <th className="py-3 px-3 font-semibold">Account Status</th>
                  <th className="py-3 px-3 font-semibold">Provisioned</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                          {u.full_name[0]}
                        </div>
                        <span className="font-semibold text-slate-900">{u.full_name}</span>
                      </div>
                    </td>

                    <td className="py-3 px-3 font-medium text-slate-600 font-mono">
                      {u.email}
                    </td>

                    <td className="py-3 px-3">
                      <Badge value={u.role} />
                    </td>

                    <td className="py-3 px-3">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-300" /> Inactive
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Team Responder"
        description="Provision a new team member with either Administrator or On-Call Responder access."
      >
        <form onSubmit={handleAddUser} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Jordan Rivera"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-user-fullname"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Work Email *
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jordan@company.com"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-user-email"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Initial Password *
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-user-password"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-user-role"
            >
              <option value="RESPONDER">RESPONDER (Acknowledge, Mitigate, Update)</option>
              <option value="ADMIN">ADMIN (Full platform permissions & User admin)</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              data-testid="btn-submit-user"
            >
              Provision User
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
