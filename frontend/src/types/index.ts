export type UserRole = 'ADMIN' | 'RESPONDER';

export type ServiceHealth = 'HEALTHY' | 'DEGRADED' | 'FAILING' | 'INACTIVE';

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type IncidentStatus = 'TRIGGERED' | 'ACKNOWLEDGED' | 'MITIGATED' | 'RESOLVED';

export type AlertStatus = 'RECEIVED' | 'PROCESSED' | 'DEDUPLICATED';

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Service {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  owner_team: string;
  environment: string;
  health_status: ServiceHealth;
  escalation_policy_id?: string;
  escalation_policy_name?: string;
  is_active: boolean;
  active_incident_count: number;
  created_at: string;
  updated_at: string;
}

export interface EscalationRule {
  id: string;
  escalation_policy_id: string;
  level_number: number;
  user_id: string;
  user_name?: string;
  user_email?: string;
  created_at: string;
}

export interface EscalationPolicy {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  ack_timeout_seconds: number;
  is_active: boolean;
  rules: EscalationRule[];
  created_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  actor_id?: string;
  actor_name: string;
  message: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface IncidentUpdate {
  id: string;
  incident_id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
  message: string;
  created_at: string;
}

export interface Alert {
  id: string;
  organization_id: string;
  service_id: string;
  service_name?: string;
  incident_id?: string;
  external_id?: string;
  fingerprint: string;
  title: string;
  description?: string;
  severity: Severity;
  source: string;
  status: AlertStatus;
  payload?: Record<string, any>;
  received_at: string;
}

export interface Incident {
  id: string;
  incident_number: number;
  organization_id: string;
  service_id: string;
  service_name?: string;
  title: string;
  description?: string;
  severity: Severity;
  status: IncidentStatus;
  assigned_responder_id?: string;
  assigned_responder_name?: string;
  escalation_policy_id?: string;
  escalation_policy_name?: string;
  current_escalation_level: number;
  ack_deadline?: string;
  acknowledged_at?: string;
  mitigated_at?: string;
  resolved_at?: string;
  alert_count: number;
  fingerprint: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentDetail extends Incident {
  events: IncidentEvent[];
  alerts: Alert[];
  updates: IncidentUpdate[];
}

export interface DashboardSummary {
  active_incidents: number;
  critical_incidents: number;
  unacknowledged_incidents: number;
  resolved_incidents: number;
  total_services: number;
  degraded_or_failing_services: number;
}

export interface IncidentTrendItem {
  date: string;
  total: number;
  critical: number;
  high: number;
  resolved: number;
}

export interface ServiceHealthItem {
  id: string;
  name: string;
  environment: string;
  owner_team: string;
  health_status: ServiceHealth;
  active_incident_count: number;
}

export interface SeverityDistributionItem {
  name: string;
  value: number;
  color: string;
}

export interface DashboardData {
  summary: DashboardSummary;
  trends: IncidentTrendItem[];
  service_health: ServiceHealthItem[];
  severity_distribution: SeverityDistributionItem[];
  recent_incidents: Incident[];
}

export interface AuditEvent {
  id: string;
  organization_id: string;
  actor_id?: string;
  actor_email: string;
  event_type: string;
  target_type: string;
  target_id?: string;
  details: string;
  created_at: string;
}
