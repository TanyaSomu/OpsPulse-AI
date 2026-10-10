import axios from 'axios';
import type {
  User,
  Service,
  Incident,
  IncidentDetail,
  Alert,
  EscalationPolicy,
  DashboardData,
  AuditEvent,
  Severity,
  IncidentStatus,
  ServiceHealth,
  UserRole
} from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('opspulse_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('opspulse_token');
      localStorage.removeItem('opspulse_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const res = await api.post<{ access_token: string; token_type: string; user: User }>('/auth/login', credentials);
    return res.data;
  },
  register: async (payload: { email: string; password: string; full_name: string; role?: UserRole }) => {
    const res = await api.post<User>('/auth/register', payload);
    return res.data;
  },
  getMe: async () => {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
};

export const dashboardApi = {
  getData: async () => {
    const res = await api.get<DashboardData>('/dashboard/data');
    return res.data;
  },
};

export const incidentsApi = {
  list: async (params?: {
    status?: IncidentStatus;
    severity?: Severity;
    service_id?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) => {
    const res = await api.get<Incident[]>('/incidents', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get<IncidentDetail>(`/incidents/${id}`);
    return res.data;
  },
  create: async (payload: {
    service_id: string;
    title: string;
    description?: string;
    severity: Severity;
    assigned_responder_id?: string;
    escalation_policy_id?: string;
  }) => {
    const res = await api.post<Incident>('/incidents', payload);
    return res.data;
  },
  update: async (id: string, payload: {
    title?: string;
    description?: string;
    severity?: Severity;
    assigned_responder_id?: string;
  }) => {
    const res = await api.patch<Incident>(`/incidents/${id}`, payload);
    return res.data;
  },
  acknowledge: async (id: string) => {
    const res = await api.post<Incident>(`/incidents/${id}/acknowledge`);
    return res.data;
  },
  assign: async (id: string, userId: string) => {
    const res = await api.post<Incident>(`/incidents/${id}/assign`, { user_id: userId });
    return res.data;
  },
  mitigate: async (id: string, message?: string) => {
    const res = await api.post<Incident>(`/incidents/${id}/mitigate`, message ? { message } : {});
    return res.data;
  },
  resolve: async (id: string, message?: string) => {
    const res = await api.post<Incident>(`/incidents/${id}/resolve`, message ? { message } : {});
    return res.data;
  },
  reopen: async (id: string, message?: string) => {
    const res = await api.post<Incident>(`/incidents/${id}/reopen`, message ? { message } : {});
    return res.data;
  },
  postUpdate: async (id: string, message: string) => {
    const res = await api.post(`/incidents/${id}/updates`, { message });
    return res.data;
  },
  checkEscalations: async () => {
    const res = await api.post('/incidents/check-escalations');
    return res.data;
  },
};

export const alertsApi = {
  list: async (params?: { service_id?: string; status?: string; severity?: Severity }) => {
    const res = await api.get<Alert[]>('/alerts', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get<Alert>(`/alerts/${id}`);
    return res.data;
  },
  simulateWebhook: async (payload: {
    service_id?: string;
    service_name?: string;
    title: string;
    description?: string;
    severity: Severity;
    source?: string;
    metadata?: Record<string, any>;
  }) => {
    const res = await api.post('/alerts/webhook', payload);
    return res.data;
  },
};

export const servicesApi = {
  list: async (params?: { health_status?: ServiceHealth }) => {
    const res = await api.get<Service[]>('/services', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get<Service>(`/services/${id}`);
    return res.data;
  },
  create: async (payload: {
    name: string;
    description?: string;
    owner_team: string;
    environment: string;
    health_status: ServiceHealth;
    escalation_policy_id?: string;
    is_active?: boolean;
  }) => {
    const res = await api.post<Service>('/services', payload);
    return res.data;
  },
  update: async (id: string, payload: Partial<Service>) => {
    const res = await api.patch<Service>(`/services/${id}`, payload);
    return res.data;
  },
  delete: async (id: string) => {
    await api.delete(`/services/${id}`);
  },
};

export const escalationApi = {
  list: async () => {
    const res = await api.get<EscalationPolicy[]>('/escalation-policies');
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get<EscalationPolicy>(`/escalation-policies/${id}`);
    return res.data;
  },
  create: async (payload: {
    name: string;
    description?: string;
    ack_timeout_seconds: number;
    rules: { level_number: number; user_id: string }[];
  }) => {
    const res = await api.post<EscalationPolicy>('/escalation-policies', payload);
    return res.data;
  },
  update: async (id: string, payload: Partial<EscalationPolicy>) => {
    const res = await api.patch<EscalationPolicy>(`/escalation-policies/${id}`, payload);
    return res.data;
  },
  delete: async (id: string) => {
    await api.delete(`/escalation-policies/${id}`);
  },
};

export const usersApi = {
  list: async () => {
    const res = await api.get<User[]>('/users');
    return res.data;
  },
  create: async (payload: {
    email: string;
    full_name: string;
    password: string;
    role: UserRole;
  }) => {
    const res = await api.post<User>('/users', payload);
    return res.data;
  },
  update: async (id: string, payload: {
    full_name?: string;
    role?: UserRole;
    is_active?: boolean;
    password?: string;
  }) => {
    const res = await api.patch<User>(`/users/${id}`, payload);
    return res.data;
  },
};

export const auditApi = {
  list: async (params?: { target_type?: string; event_type?: string; page?: number; limit?: number }) => {
    const res = await api.get<AuditEvent[]>('/audit-events', { params });
    return res.data;
  },
};

export default api;
