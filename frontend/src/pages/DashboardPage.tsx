import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Flame,
  Clock,
  CheckCircle2,
  Server,
  ArrowUpRight,
  TrendingUp,
  PieChart as PieIcon,
  Plus
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { dashboardApi } from '../services/api';
import type { DashboardData } from '../types';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setError(null);
      const res = await dashboardApi.getData();
      setData(res);
    } catch {
      setError('Failed to load dashboard metrics from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Listen to global simulation refresh events
    const handleRefresh = () => fetchDashboardData();
    window.addEventListener('opspulse-data-refresh', handleRefresh);
    return () => window.removeEventListener('opspulse-data-refresh', handleRefresh);
  }, []);

  if (isLoading) {
    return <LoadingSpinner message="Aggregating service reliability metrics..." />;
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center">
        <p className="text-sm font-semibold text-red-700">{error || 'Data unavailable'}</p>
        <Button variant="outline" size="sm" onClick={fetchDashboardData} className="mt-3">
          Retry
        </Button>
      </div>
    );
  }

  const { summary, trends, service_health, severity_distribution, recent_incidents } = data;

  const statCards = [
    {
      title: 'Active Incidents',
      value: summary.active_incidents,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      testId: 'stat-active-incidents',
    },
    {
      title: 'Critical (P1)',
      value: summary.critical_incidents,
      icon: Flame,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      testId: 'stat-critical-incidents',
    },
    {
      title: 'Awaiting Ack',
      value: summary.unacknowledged_incidents,
      icon: Clock,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      testId: 'stat-unack-incidents',
    },
    {
      title: 'Resolved (Past 7d)',
      value: summary.resolved_incidents,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      testId: 'stat-resolved-incidents',
    },
    {
      title: 'Monitored Services',
      value: summary.total_services,
      icon: Server,
      color: 'text-slate-700',
      bgColor: 'bg-slate-100',
      borderColor: 'border-slate-200',
      testId: 'stat-total-services',
    },
    {
      title: 'Impacted Services',
      value: summary.degraded_or_failing_services,
      icon: AlertTriangle,
      color: summary.degraded_or_failing_services > 0 ? 'text-red-600' : 'text-emerald-600',
      bgColor: summary.degraded_or_failing_services > 0 ? 'bg-red-50' : 'bg-emerald-50',
      borderColor: summary.degraded_or_failing_services > 0 ? 'border-red-200' : 'border-emerald-200',
      testId: 'stat-failing-services',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header and Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
            Service Reliability Dashboard
          </h1>
          <p className="text-xs md:text-sm text-slate-500 mt-0.5">
            Real-time incident response, SLA tracking, and service telemetry overview.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/incidents')}
            icon={<Plus className="w-4 h-4" />}
            data-testid="btn-dashboard-new-incident"
          >
            Manage Incidents
          </Button>
        </div>
      </div>

      {/* 6 Metric KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className={`p-4 rounded-xl bg-white border ${card.borderColor} shadow-xs transition-shadow hover:shadow-md`}
              data-testid={card.testId}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider truncate">
                  {card.title}
                </span>
                <div className={`p-1.5 rounded-lg ${card.bgColor} ${card.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-slate-900">
                  {card.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Visual Charts: 7-Day Trend + Severity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Bar Chart */}
        <div className="lg:col-span-2 p-5 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-semibold text-slate-800">7-Day Incident Ingestion Volume</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">Real-time DB query</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="critical" name="Critical (P1)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="high" name="High (P2)" fill="#f97316" radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution Donut */}
        <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-semibold text-slate-800">Active Severity Breakdown</h2>
            </div>
          </div>
          <div className="h-52 w-full flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severity_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {severity_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
            {severity_distribution.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-600 truncate">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.name}
                </span>
                <span className="font-semibold text-slate-800">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Services Health Grid */}
      <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-semibold text-slate-800">Registered Services Health Summary</h2>
          </div>
          <button
            onClick={() => navigate('/services')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
          >
            All Services <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {service_health.map((svc) => (
            <div
              key={svc.id}
              onClick={() => navigate(`/services`)}
              className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between cursor-pointer"
            >
              <div className="overflow-hidden pr-2">
                <p className="text-xs font-semibold text-slate-800 truncate">{svc.name}</p>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                  {svc.environment} • {svc.owner_team}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <Badge value={svc.health_status} />
                {svc.active_incident_count > 0 && (
                  <span className="text-[10px] font-semibold text-red-600">
                    {svc.active_incident_count} active
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-semibold text-slate-800">Recent Incident Activity</h2>
          </div>
          <button
            onClick={() => navigate('/incidents')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 cursor-pointer"
          >
            View All <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/60">
                <th className="py-2.5 px-3 font-semibold">Incident</th>
                <th className="py-2.5 px-3 font-semibold">Severity</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Affected Service</th>
                <th className="py-2.5 px-3 font-semibold">Responder</th>
                <th className="py-2.5 px-3 font-semibold">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent_incidents.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => navigate(`/incidents/${inc.id}`)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3">
                    <span className="font-mono font-semibold text-indigo-600 group-hover:underline">
                      #{inc.incident_number}
                    </span>
                    <span className="font-medium text-slate-800 ml-2">{inc.title}</span>
                  </td>
                  <td className="py-3 px-3">
                    <Badge value={inc.severity} />
                  </td>
                  <td className="py-3 px-3">
                    <Badge value={inc.status} />
                  </td>
                  <td className="py-3 px-3 font-medium text-slate-600">
                    {inc.service_name}
                  </td>
                  <td className="py-3 px-3 text-slate-500">
                    {inc.assigned_responder_name || <span className="italic text-slate-400">Unassigned</span>}
                  </td>
                  <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                    {new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
