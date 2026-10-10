import React from 'react';
import type { Severity, IncidentStatus, ServiceHealth, UserRole, AlertStatus } from '../../types';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'severity' | 'status' | 'health' | 'role' | 'alert_status' | 'neutral';
  value?: Severity | IncidentStatus | ServiceHealth | UserRole | AlertStatus | string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  value,
  className = '',
  size = 'sm',
}) => {
  const displayVal = children || value;
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  const getColorClasses = () => {
    const val = String(value || children).toUpperCase();

    // Severity mapping: Red for critical, Orange for high, Yellow for medium, Blue for low/info
    if (val === 'CRITICAL') {
      return 'bg-red-50 text-red-700 border-red-200 ring-1 ring-red-400/20';
    }
    if (val === 'HIGH') {
      return 'bg-orange-50 text-orange-700 border-orange-200 ring-1 ring-orange-400/20';
    }
    if (val === 'MEDIUM') {
      return 'bg-amber-50 text-amber-700 border-amber-200 ring-1 ring-amber-400/20';
    }
    if (val === 'LOW' || val === 'INFO') {
      return 'bg-blue-50 text-blue-700 border-blue-200 ring-1 ring-blue-400/20';
    }

    // Incident Status: Red triggered, Yellow acknowledged, Blue mitigated, Green resolved
    if (val === 'TRIGGERED') {
      return 'bg-red-100 text-red-800 border-red-300 font-semibold animate-pulse';
    }
    if (val === 'ACKNOWLEDGED') {
      return 'bg-amber-100 text-amber-800 border-amber-300 font-medium';
    }
    if (val === 'MITIGATED') {
      return 'bg-indigo-50 text-indigo-700 border-indigo-200 font-medium';
    }
    if (val === 'RESOLVED') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium';
    }

    // Service Health: Green healthy, Amber degraded, Red failing, Slate inactive
    if (val === 'HEALTHY') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (val === 'DEGRADED') {
      return 'bg-amber-50 text-amber-700 border-amber-200';
    }
    if (val === 'FAILING') {
      return 'bg-red-50 text-red-700 border-red-200';
    }
    if (val === 'INACTIVE') {
      return 'bg-slate-100 text-slate-600 border-slate-200';
    }

    // Role
    if (val === 'ADMIN') {
      return 'bg-purple-50 text-purple-700 border-purple-200 font-medium';
    }
    if (val === 'RESPONDER') {
      return 'bg-slate-100 text-slate-700 border-slate-200';
    }

    // Alert Status
    if (val === 'PROCESSED') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (val === 'DEDUPLICATED') {
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    }
    if (val === 'RECEIVED') {
      return 'bg-slate-100 text-slate-700 border-slate-200';
    }

    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border font-medium ${getColorClasses()} ${sizeClasses} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {displayVal}
    </span>
  );
};
