from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary, IncidentTrendItem, ServiceHealthItem,
    SeverityDistributionItem, DashboardDataResponse
)
from app.services.dashboard_service import (
    get_dashboard_summary, get_incident_trends,
    get_service_health_summary, get_severity_distribution,
    get_complete_dashboard_data
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve high-level incident and service metrics."""
    return get_dashboard_summary(db, current_user.organization_id)

@router.get("/incident-trends", response_model=List[IncidentTrendItem])
def get_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical incident volume trends over the requested number of days."""
    return get_incident_trends(db, current_user.organization_id, days=days)

@router.get("/service-health", response_model=List[ServiceHealthItem])
def get_services_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve health overview across all monitored services."""
    return get_service_health_summary(db, current_user.organization_id)

@router.get("/severity-distribution", response_model=List[SeverityDistributionItem])
def get_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve distribution breakdown of active incidents by severity."""
    return get_severity_distribution(db, current_user.organization_id)

@router.get("/data", response_model=DashboardDataResponse)
def get_all_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregated data bundle for the primary command dashboard."""
    return get_complete_dashboard_data(db, current_user.organization_id)
