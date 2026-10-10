import React, { useState } from 'react';
import { Menu, LogOut, BellRing, Clock, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { incidentsApi } from '../../services/api';

interface TopBarProps {
  onToggleSidebar: () => void;
  onOpenAlertModal: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  onToggleSidebar,
  onOpenAlertModal,
}) => {
  const { user, logout } = useAuth();
  const [isEscalating, setIsEscalating] = useState(false);
  const [escalationNotice, setEscalationNotice] = useState<string | null>(null);

  const handleManualEscalationCheck = async () => {
    setIsEscalating(true);
    try {
      const res = await incidentsApi.checkEscalations();
      const count = res.escalated_count || 0;
      setEscalationNotice(count > 0 ? `Escalated ${count} incident(s)` : 'SLA checked: all within deadline');
      setTimeout(() => setEscalationNotice(null), 4000);
    } catch {
      setEscalationNotice('Failed to check escalation');
      setTimeout(() => setEscalationNotice(null), 3000);
    } finally {
      setIsEscalating(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-8 bg-white border-b border-slate-200">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-500 rounded-lg hover:bg-slate-100 md:hidden cursor-pointer"
          aria-label="Toggle sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-500">
          <span>Acme Cloud Infrastructure</span>
          <span className="text-slate-300">/</span>
          <span className="text-slate-900 font-semibold">Incident Command</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {escalationNotice && (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-full border border-emerald-200 animate-fade-in">
            <CheckCircle className="w-3.5 h-3.5" />
            {escalationNotice}
          </div>
        )}

        {/* Quick action: Trigger SLA Check */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleManualEscalationCheck}
          isLoading={isEscalating}
          icon={<Clock className="w-3.5 h-3.5 text-slate-500" />}
          data-testid="btn-check-escalation"
        >
          Check SLA
        </Button>

        {/* Quick action: Simulate Webhook Alert */}
        <Button
          variant="secondary"
          size="sm"
          onClick={onOpenAlertModal}
          icon={<BellRing className="w-3.5 h-3.5 text-indigo-400" />}
          data-testid="btn-simulate-alert"
        >
          Simulate Alert
        </Button>

        {/* User profile & logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="hidden md:flex flex-col text-right">
            <span className="text-xs font-semibold text-slate-800">{user?.full_name}</span>
            <span className="text-[10px] text-slate-400">{user?.email}</span>
          </div>
          {user?.role && <Badge value={user.role} />}
          <button
            onClick={logout}
            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors cursor-pointer"
            title="Log out"
            aria-label="Log out"
            data-testid="btn-logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
