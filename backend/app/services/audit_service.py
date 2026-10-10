from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.models.user import User

def record_audit_event(
    db: Session,
    organization_id: str,
    event_type: str,
    target_type: str,
    details: str,
    actor: Optional[User] = None,
    target_id: Optional[str] = None
) -> AuditEvent:
    actor_id = actor.id if actor else None
    actor_email = actor.email if actor else "system@opspulse.local"

    audit_event = AuditEvent(
        organization_id=organization_id,
        actor_id=actor_id,
        actor_email=actor_email,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(audit_event)
    return audit_event
