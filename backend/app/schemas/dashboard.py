from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.enums import ServiceHealth
from app.schemas.incident import IncidentResponse

class DashboardSummary(BaseModel):
    active_incidents: int
    critical_incidents: int
    unacknowledged_incidents: int
    resolved_incidents: int
    total_services: int
    degraded_or_failing_services: int

class IncidentTrendItem(BaseModel):
    date: str
    total: int
    critical: int
    high: int
    resolved: int

class ServiceHealthSummary(BaseModel):
    healthy: int
    degraded: int
    failing: int
    inactive: int

class ServiceHealthItem(BaseModel):
    id: str
    name: str
    environment: str
    owner_team: str
    health_status: ServiceHealth
    active_incident_count: int

class SeverityDistributionItem(BaseModel):
    name: str
    value: int
    color: str

class DashboardDataResponse(BaseModel):
    summary: DashboardSummary
    trends: List[IncidentTrendItem]
    service_health: List[ServiceHealthItem]
    severity_distribution: List[SeverityDistributionItem]
    recent_incidents: List[IncidentResponse]
