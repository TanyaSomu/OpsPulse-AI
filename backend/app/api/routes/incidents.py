from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, cast, String
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_responder
from app.models.user import User
from app.models.incident import Incident, IncidentEvent
from app.models.enums import IncidentStatus, Severity
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentAssignRequest,
    IncidentNoteCreate, IncidentResponse, IncidentDetailResponse,
    IncidentEventResponse, IncidentUpdateResponse
)
from app.services.incident_service import (
    create_incident, acknowledge_incident, mitigate_incident,
    resolve_incident, reopen_incident, assign_incident,
    change_severity, add_incident_update,
    format_incident_response, format_incident_detail_response
)
from app.services.escalation_service import check_and_escalate_incidents

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[IncidentStatus] = None,
    severity: Optional[Severity] = None,
    service_id: Optional[str] = None,
    assigned_responder_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List and filter incidents for the current organization."""
    query = db.query(Incident).filter(Incident.organization_id == current_user.organization_id)

    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if service_id:
        query = query.filter(Incident.service_id == service_id)
    if assigned_responder_id:
        query = query.filter(Incident.assigned_responder_id == assigned_responder_id)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Incident.title.ilike(search_filter),
                Incident.description.ilike(search_filter),
                cast(Incident.incident_number, String).ilike(search_filter)
            )
        )

    offset = (page - 1) * limit
    incidents = query.order_by(desc(Incident.created_at)).offset(offset).limit(limit).all()
    return [format_incident_response(inc) for inc in incidents]

@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_new_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Create a new manual incident."""
    incident = create_incident(db, payload, current_user)
    return format_incident_response(incident)

@router.post("/check-escalations")
def trigger_escalation_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger an on-demand escalation evaluation pass across unacknowledged incidents."""
    result = check_and_escalate_incidents(db)
    return result

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve complete incident details, including timeline events and alerts."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.organization_id == current_user.organization_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return format_incident_detail_response(incident)

@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Update incident metadata, severity, or assignment."""
    incident = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.organization_id == current_user.organization_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if payload.severity and payload.severity != incident.severity:
        incident = change_severity(db, incident.id, payload.severity, current_user)

    if payload.assigned_responder_id and payload.assigned_responder_id != incident.assigned_responder_id:
        incident = assign_incident(db, incident.id, payload.assigned_responder_id, current_user)

    if payload.title:
        incident.title = payload.title
    if payload.description is not None:
        incident.description = payload.description

    db.commit()
    db.refresh(incident)
    return format_incident_response(incident)

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Acknowledge incident, halting SLA deadline countdown."""
    incident = acknowledge_incident(db, incident_id, current_user)
    return format_incident_response(incident)

@router.post("/{incident_id}/assign", response_model=IncidentResponse)
def assign(
    incident_id: str,
    payload: IncidentAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Assign or reassign an incident to a specific responder."""
    incident = assign_incident(db, incident_id, payload.user_id, current_user)
    return format_incident_response(incident)

@router.post("/{incident_id}/mitigate", response_model=IncidentResponse)
def mitigate(
    incident_id: str,
    payload: Optional[IncidentNoteCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Mark an incident as mitigated."""
    note = payload.message if payload else None
    incident = mitigate_incident(db, incident_id, current_user, note=note)
    return format_incident_response(incident)

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve(
    incident_id: str,
    payload: Optional[IncidentNoteCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Resolve an incident and restore service health if all active issues are addressed."""
    note = payload.message if payload else None
    incident = resolve_incident(db, incident_id, current_user, note=note)
    return format_incident_response(incident)

@router.post("/{incident_id}/reopen", response_model=IncidentResponse)
def reopen(
    incident_id: str,
    payload: Optional[IncidentNoteCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Reopen a previously resolved incident."""
    note = payload.message if payload else None
    incident = reopen_incident(db, incident_id, current_user, note=note)
    return format_incident_response(incident)

@router.post("/{incident_id}/updates", response_model=IncidentUpdateResponse)
def post_update(
    incident_id: str,
    payload: IncidentNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responder)
):
    """Post an investigation note or status update to the incident thread."""
    update = add_incident_update(db, incident_id, payload.message, current_user)
    return IncidentUpdateResponse(
        id=update.id,
        incident_id=update.incident_id,
        user_id=update.user_id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        message=update.message,
        created_at=update.created_at
    )

@router.get("/{incident_id}/events", response_model=List[IncidentEventResponse])
def get_incident_events(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve immutable timeline events for an incident."""
    events = db.query(IncidentEvent).filter(
        IncidentEvent.incident_id == incident_id
    ).order_by(desc(IncidentEvent.created_at)).all()
    return events
