from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status
from app.models.incident import Incident, IncidentEvent, IncidentAssignment, IncidentUpdate
from app.models.service import Service
from app.models.user import User
from app.models.escalation import EscalationPolicy
from app.models.notification import Notification
from app.models.enums import IncidentStatus, Severity, ServiceHealth
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate as IncidentUpdateSchema,
    IncidentResponse, IncidentDetailResponse, IncidentEventResponse,
    IncidentUpdateResponse
)
from app.schemas.alert import AlertResponse
from app.services.audit_service import record_audit_event
from app.services.alert_service import generate_alert_fingerprint

VALID_TRANSITIONS = {
    IncidentStatus.TRIGGERED: {
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.ACKNOWLEDGED: {
        IncidentStatus.MITIGATED,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.MITIGATED: {
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.TRIGGERED,  # Reopening supported
    },
}

def validate_state_transition(current_status: IncidentStatus, target_status: IncidentStatus):
    if current_status == target_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident is already in '{current_status.value}' state."
        )
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from '{current_status.value}' to '{target_status.value}'."
        )

def update_service_health_after_incident_change(db: Session, service_id: str):
    """Re-evaluate service health based on remaining active incidents."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service or not service.is_active:
        return

    active_incidents = db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.status != IncidentStatus.RESOLVED
    ).all()

    if not active_incidents:
        service.health_status = ServiceHealth.HEALTHY
    else:
        has_critical_or_high = any(inc.severity in [Severity.CRITICAL, Severity.HIGH] for inc in active_incidents)
        if has_critical_or_high:
            service.health_status = ServiceHealth.FAILING
        else:
            service.health_status = ServiceHealth.DEGRADED

def format_incident_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse(
        id=incident.id,
        incident_number=incident.incident_number,
        organization_id=incident.organization_id,
        service_id=incident.service_id,
        service_name=incident.service.name if incident.service else None,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        assigned_responder_id=incident.assigned_responder_id,
        assigned_responder_name=incident.assigned_responder.full_name if incident.assigned_responder else None,
        escalation_policy_id=incident.escalation_policy_id,
        escalation_policy_name=incident.escalation_policy.name if incident.escalation_policy else None,
        current_escalation_level=incident.current_escalation_level,
        ack_deadline=incident.ack_deadline,
        acknowledged_at=incident.acknowledged_at,
        mitigated_at=incident.mitigated_at,
        resolved_at=incident.resolved_at,
        alert_count=incident.alert_count,
        fingerprint=incident.fingerprint,
        created_at=incident.created_at,
        updated_at=incident.updated_at
    )

def format_incident_detail_response(incident: Incident) -> IncidentDetailResponse:
    base = format_incident_response(incident)

    events = [
        IncidentEventResponse(
            id=e.id,
            incident_id=e.incident_id,
            event_type=e.event_type,
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            message=e.message,
            metadata_json=e.metadata_json,
            created_at=e.created_at
        )
        for e in incident.events
    ]

    updates = [
        IncidentUpdateResponse(
            id=u.id,
            incident_id=u.incident_id,
            user_id=u.user_id,
            user_name=u.user.full_name if u.user else None,
            user_email=u.user.email if u.user else None,
            message=u.message,
            created_at=u.created_at
        )
        for u in incident.updates
    ]

    alerts = [
        AlertResponse(
            id=a.id,
            organization_id=a.organization_id,
            service_id=a.service_id,
            service_name=incident.service.name if incident.service else None,
            incident_id=a.incident_id,
            external_id=a.external_id,
            fingerprint=a.fingerprint,
            title=a.title,
            description=a.description,
            severity=a.severity,
            source=a.source,
            status=a.status,
            payload=a.payload,
            received_at=a.received_at
        )
        for a in incident.alerts
    ]

    return IncidentDetailResponse(
        **base.model_dump(),
        events=events,
        updates=updates,
        alerts=alerts
    )

def create_incident(db: Session, incident_in: IncidentCreate, user: User) -> Incident:
    service = db.query(Service).filter(Service.id == incident_in.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    now = datetime.now(timezone.utc)
    policy_id = incident_in.escalation_policy_id or service.escalation_policy_id
    policy = db.query(EscalationPolicy).filter(EscalationPolicy.id == policy_id).first() if policy_id else None

    timeout_seconds = policy.ack_timeout_seconds if policy else 300
    ack_deadline = now + timedelta(seconds=timeout_seconds)

    fingerprint = generate_alert_fingerprint(
        service_id=service.id,
        title=incident_in.title,
        source="Manual Creation"
    )

    max_num = db.query(func.max(Incident.incident_number)).scalar() or 1000
    incident_number = max_num + 1

    responder_id = incident_in.assigned_responder_id
    if not responder_id and policy and policy.rules:
        responder_id = min(policy.rules, key=lambda r: r.level_number).user_id

    incident = Incident(
        incident_number=incident_number,
        organization_id=user.organization_id,
        service_id=service.id,
        title=incident_in.title,
        description=incident_in.description,
        severity=incident_in.severity,
        status=IncidentStatus.TRIGGERED,
        assigned_responder_id=responder_id,
        escalation_policy_id=policy.id if policy else None,
        current_escalation_level=1,
        ack_deadline=ack_deadline,
        alert_count=1,
        fingerprint=fingerprint,
        created_at=now,
        updated_at=now
    )
    db.add(incident)
    db.flush()

    # Update service health
    if incident_in.severity in [Severity.CRITICAL, Severity.HIGH]:
        service.health_status = ServiceHealth.FAILING
    else:
        if service.health_status == ServiceHealth.HEALTHY:
            service.health_status = ServiceHealth.DEGRADED

    # Event
    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="TRIGGERED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=f"Incident #{incident.incident_number} created manually by {user.full_name}.",
        metadata_json={"severity": incident.severity.value}
    ))

    record_audit_event(
        db=db,
        organization_id=user.organization_id,
        actor=user,
        event_type="INCIDENT_CREATED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} '{incident.title}' created manually."
    )

    db.commit()
    db.refresh(incident)
    return incident

def acknowledge_incident(db: Session, incident_id: str, user: User) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validate_state_transition(incident.status, IncidentStatus.ACKNOWLEDGED)

    now = datetime.now(timezone.utc)
    incident.status = IncidentStatus.ACKNOWLEDGED
    incident.acknowledged_at = now
    incident.ack_deadline = None  # Cleared on ack
    incident.updated_at = now

    # Auto assign to acknowledger if unassigned
    if not incident.assigned_responder_id:
        incident.assigned_responder_id = user.id
        db.add(IncidentAssignment(
            incident_id=incident.id,
            user_id=user.id,
            assigned_by_id=user.id,
            assigned_at=now
        ))

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="ACKNOWLEDGED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=f"Incident acknowledged by {user.full_name} ({user.email}). SLA timer stopped."
    ))

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=user,
        event_type="INCIDENT_ACKNOWLEDGED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} acknowledged by {user.full_name}."
    )

    db.commit()
    db.refresh(incident)
    return incident

def mitigate_incident(db: Session, incident_id: str, user: User, note: Optional[str] = None) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validate_state_transition(incident.status, IncidentStatus.MITIGATED)

    now = datetime.now(timezone.utc)
    incident.status = IncidentStatus.MITIGATED
    incident.mitigated_at = now
    incident.updated_at = now

    msg = f"Incident marked as mitigated by {user.full_name}."
    if note:
        msg += f" Note: {note}"

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="MITIGATED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=msg
    ))

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=user,
        event_type="INCIDENT_MITIGATED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} mitigated."
    )

    db.commit()
    db.refresh(incident)
    return incident

def resolve_incident(db: Session, incident_id: str, user: User, note: Optional[str] = None) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validate_state_transition(incident.status, IncidentStatus.RESOLVED)

    now = datetime.now(timezone.utc)
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = now
    incident.ack_deadline = None
    incident.updated_at = now

    msg = f"Incident resolved by {user.full_name}."
    if note:
        msg += f" Resolution: {note}"

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="RESOLVED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=msg
    ))

    update_service_health_after_incident_change(db, incident.service_id)

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=user,
        event_type="INCIDENT_RESOLVED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} resolved by {user.full_name}."
    )

    db.commit()
    db.refresh(incident)
    return incident

def reopen_incident(db: Session, incident_id: str, user: User, note: Optional[str] = None) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validate_state_transition(incident.status, IncidentStatus.TRIGGERED)

    now = datetime.now(timezone.utc)
    policy = incident.escalation_policy
    timeout_seconds = policy.ack_timeout_seconds if policy else 300

    incident.status = IncidentStatus.TRIGGERED
    incident.resolved_at = None
    incident.mitigated_at = None
    incident.acknowledged_at = None
    incident.ack_deadline = now + timedelta(seconds=timeout_seconds)
    incident.updated_at = now

    msg = f"Incident reopened by {user.full_name}."
    if note:
        msg += f" Reason: {note}"

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="REOPENED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=msg
    ))

    update_service_health_after_incident_change(db, incident.service_id)

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=user,
        event_type="INCIDENT_REOPENED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} reopened by {user.full_name}."
    )

    db.commit()
    db.refresh(incident)
    return incident

def assign_incident(db: Session, incident_id: str, target_user_id: str, actor: User) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target responder user not found")

    now = datetime.now(timezone.utc)
    old_responder_name = incident.assigned_responder.full_name if incident.assigned_responder else "Unassigned"
    incident.assigned_responder_id = target_user.id
    incident.updated_at = now

    db.add(IncidentAssignment(
        incident_id=incident.id,
        user_id=target_user.id,
        assigned_by_id=actor.id,
        assigned_at=now
    ))

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="ASSIGNED",
        actor_id=actor.id,
        actor_name=actor.full_name,
        message=f"Incident reassigned from {old_responder_name} to {target_user.full_name} by {actor.full_name}."
    ))

    # Notify new responder
    db.add(Notification(
        incident_id=incident.id,
        user_id=target_user.id,
        channel="APP_NOTIFICATION",
        title=f"Incident Assigned #{incident.incident_number}",
        body=f"You have been assigned to incident '{incident.title}' by {actor.full_name}.",
        status="DELIVERED"
    ))

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=actor,
        event_type="INCIDENT_ASSIGNED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} reassigned to {target_user.full_name}."
    )

    db.commit()
    db.refresh(incident)
    return incident

def change_severity(db: Session, incident_id: str, new_severity: Severity, actor: User) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_severity = incident.severity
    if old_severity == new_severity:
        return incident

    now = datetime.now(timezone.utc)
    incident.severity = new_severity
    incident.updated_at = now

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="SEVERITY_CHANGED",
        actor_id=actor.id,
        actor_name=actor.full_name,
        message=f"Severity changed from {old_severity.value} to {new_severity.value} by {actor.full_name}."
    ))

    update_service_health_after_incident_change(db, incident.service_id)

    record_audit_event(
        db=db,
        organization_id=incident.organization_id,
        actor=actor,
        event_type="INCIDENT_SEVERITY_CHANGED",
        target_type="INCIDENT",
        target_id=incident.id,
        details=f"Incident #{incident.incident_number} severity updated to {new_severity.value}."
    )

    db.commit()
    db.refresh(incident)
    return incident

def add_incident_update(db: Session, incident_id: str, message: str, user: User) -> IncidentUpdate:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    now = datetime.now(timezone.utc)
    update = IncidentUpdate(
        incident_id=incident.id,
        user_id=user.id,
        message=message,
        created_at=now
    )
    db.add(update)

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="UPDATE_POSTED",
        actor_id=user.id,
        actor_name=user.full_name,
        message=f"Investigation update by {user.full_name}: {message}"
    ))

    db.commit()
    db.refresh(update)
    return update
