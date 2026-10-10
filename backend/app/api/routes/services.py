from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.service import Service
from app.models.incident import Incident
from app.models.enums import IncidentStatus, ServiceHealth
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/services", tags=["Services"])

def format_service_response(db: Session, s: Service) -> ServiceResponse:
    active_inc_count = db.query(func.count(Incident.id)).filter(
        Incident.service_id == s.id,
        Incident.status != IncidentStatus.RESOLVED
    ).scalar() or 0

    return ServiceResponse(
        id=s.id,
        organization_id=s.organization_id,
        name=s.name,
        slug=s.slug,
        description=s.description,
        owner_team=s.owner_team,
        environment=s.environment,
        health_status=s.health_status,
        escalation_policy_id=s.escalation_policy_id,
        escalation_policy_name=s.escalation_policy.name if s.escalation_policy else None,
        is_active=s.is_active,
        active_incident_count=active_inc_count,
        created_at=s.created_at,
        updated_at=s.updated_at
    )

@router.get("", response_model=List[ServiceResponse])
def list_services(
    environment: Optional[str] = None,
    health_status: Optional[ServiceHealth] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all monitored services."""
    query = db.query(Service).filter(Service.organization_id == current_user.organization_id)

    if environment:
        query = query.filter(Service.environment == environment)
    if health_status:
        query = query.filter(Service.health_status == health_status)
    if is_active is not None:
        query = query.filter(Service.is_active == is_active)

    services = query.order_by(Service.name).all()
    return [format_service_response(db, s) for s in services]

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Register a new service to monitor (Admin only)."""
    slug = payload.name.lower().replace(" ", "-")
    existing = db.query(Service).filter(
        Service.organization_id == current_user.organization_id,
        func.lower(Service.name) == payload.name.strip().lower()
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Service with this name already exists.")

    service = Service(
        organization_id=current_user.organization_id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        owner_team=payload.owner_team,
        environment=payload.environment,
        health_status=payload.health_status,
        escalation_policy_id=payload.escalation_policy_id,
        is_active=payload.is_active
    )
    db.add(service)
    db.flush()

    record_audit_event(
        db=db,
        organization_id=current_user.organization_id,
        actor=current_user,
        event_type="SERVICE_CREATED",
        target_type="SERVICE",
        target_id=service.id,
        details=f"Service '{service.name}' registered."
    )

    db.commit()
    db.refresh(service)
    return format_service_response(db, service)

@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific service."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.organization_id == current_user.organization_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return format_service_response(db, service)

@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: str,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update service configurations (Admin only)."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.organization_id == current_user.organization_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if payload.name:
        service.name = payload.name.strip()
        service.slug = payload.name.strip().lower().replace(" ", "-")
    if payload.description is not None:
        service.description = payload.description
    if payload.owner_team:
        service.owner_team = payload.owner_team
    if payload.environment:
        service.environment = payload.environment
    if payload.health_status is not None:
        service.health_status = payload.health_status
    if payload.escalation_policy_id is not None:
        service.escalation_policy_id = payload.escalation_policy_id
    if payload.is_active is not None:
        service.is_active = payload.is_active

    record_audit_event(
        db=db,
        organization_id=current_user.organization_id,
        actor=current_user,
        event_type="SERVICE_UPDATED",
        target_type="SERVICE",
        target_id=service.id,
        details=f"Service '{service.name}' updated."
    )

    db.commit()
    db.refresh(service)
    return format_service_response(db, service)

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deactivate or remove a service (Admin only)."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.organization_id == current_user.organization_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    service_name = service.name
    db.delete(service)

    record_audit_event(
        db=db,
        organization_id=current_user.organization_id,
        actor=current_user,
        event_type="SERVICE_DELETED",
        target_type="SERVICE",
        target_id=service_id,
        details=f"Service '{service_name}' removed."
    )

    db.commit()
    return None
