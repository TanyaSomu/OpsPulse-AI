from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, cast, Date
from app.models.incident import Incident
from app.models.service import Service
from app.models.enums import IncidentStatus, Severity, ServiceHealth
from app.schemas.dashboard import (
    DashboardSummary, IncidentTrendItem, ServiceHealthItem,
    SeverityDistributionItem, DashboardDataResponse
)
from app.services.incident_service import format_incident_response

def get_dashboard_summary(db: Session, organization_id: str) -> DashboardSummary:
    active_count = db.query(func.count(Incident.id)).filter(
        Incident.organization_id == organization_id,
        Incident.status != IncidentStatus.RESOLVED
    ).scalar() or 0

    critical_count = db.query(func.count(Incident.id)).filter(
        Incident.organization_id == organization_id,
        Incident.status != IncidentStatus.RESOLVED,
        Incident.severity == Severity.CRITICAL
    ).scalar() or 0

    unack_count = db.query(func.count(Incident.id)).filter(
        Incident.organization_id == organization_id,
        Incident.status == IncidentStatus.TRIGGERED
    ).scalar() or 0

    resolved_count = db.query(func.count(Incident.id)).filter(
        Incident.organization_id == organization_id,
        Incident.status == IncidentStatus.RESOLVED
    ).scalar() or 0

    total_services = db.query(func.count(Service.id)).filter(
        Service.organization_id == organization_id,
        Service.is_active == True
    ).scalar() or 0

    degraded_or_failing = db.query(func.count(Service.id)).filter(
        Service.organization_id == organization_id,
        Service.is_active == True,
        Service.health_status.in_([ServiceHealth.DEGRADED, ServiceHealth.FAILING])
    ).scalar() or 0

    return DashboardSummary(
        active_incidents=active_count,
        critical_incidents=critical_count,
        unacknowledged_incidents=unack_count,
        resolved_incidents=resolved_count,
        total_services=total_services,
        degraded_or_failing_services=degraded_or_failing
    )

def get_incident_trends(db: Session, organization_id: str, days: int = 7) -> List[IncidentTrendItem]:
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=days - 1)).date()

    trends = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        next_date = current_date + timedelta(days=1)

        total = db.query(func.count(Incident.id)).filter(
            Incident.organization_id == organization_id,
            Incident.created_at >= current_date,
            Incident.created_at < next_date
        ).scalar() or 0

        critical = db.query(func.count(Incident.id)).filter(
            Incident.organization_id == organization_id,
            Incident.severity == Severity.CRITICAL,
            Incident.created_at >= current_date,
            Incident.created_at < next_date
        ).scalar() or 0

        high = db.query(func.count(Incident.id)).filter(
            Incident.organization_id == organization_id,
            Incident.severity == Severity.HIGH,
            Incident.created_at >= current_date,
            Incident.created_at < next_date
        ).scalar() or 0

        resolved = db.query(func.count(Incident.id)).filter(
            Incident.organization_id == organization_id,
            Incident.status == IncidentStatus.RESOLVED,
            Incident.resolved_at >= current_date,
            Incident.resolved_at < next_date
        ).scalar() or 0

        trends.append(IncidentTrendItem(
            date=current_date.strftime("%b %d"),
            total=total,
            critical=critical,
            high=high,
            resolved=resolved
        ))

    return trends

def get_service_health_summary(db: Session, organization_id: str) -> List[ServiceHealthItem]:
    services = db.query(Service).filter(
        Service.organization_id == organization_id,
        Service.is_active == True
    ).order_by(Service.name).all()

    result = []
    for s in services:
        active_inc_count = db.query(func.count(Incident.id)).filter(
            Incident.service_id == s.id,
            Incident.status != IncidentStatus.RESOLVED
        ).scalar() or 0

        result.append(ServiceHealthItem(
            id=s.id,
            name=s.name,
            environment=s.environment,
            owner_team=s.owner_team,
            health_status=s.health_status,
            active_incident_count=active_inc_count
        ))

    return result

def get_severity_distribution(db: Session, organization_id: str) -> List[SeverityDistributionItem]:
    color_map = {
        Severity.CRITICAL: "#ef4444",
        Severity.HIGH: "#f97316",
        Severity.MEDIUM: "#eab308",
        Severity.LOW: "#3b82f6",
        Severity.INFO: "#64748b"
    }

    distribution = []
    for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
        count = db.query(func.count(Incident.id)).filter(
            Incident.organization_id == organization_id,
            Incident.status != IncidentStatus.RESOLVED,
            Incident.severity == sev
        ).scalar() or 0

        distribution.append(SeverityDistributionItem(
            name=sev.value,
            value=count,
            color=color_map[sev]
        ))

    return distribution

def get_complete_dashboard_data(db: Session, organization_id: str) -> DashboardDataResponse:
    summary = get_dashboard_summary(db, organization_id)
    trends = get_incident_trends(db, organization_id)
    service_health = get_service_health_summary(db, organization_id)
    severity_distribution = get_severity_distribution(db, organization_id)

    recent_incidents = db.query(Incident).filter(
        Incident.organization_id == organization_id
    ).order_by(desc(Incident.created_at)).limit(8).all()

    formatted_recent = [format_incident_response(inc) for inc in recent_incidents]

    return DashboardDataResponse(
        summary=summary,
        trends=trends,
        service_health=service_health,
        severity_distribution=severity_distribution,
        recent_incidents=formatted_recent
    )
