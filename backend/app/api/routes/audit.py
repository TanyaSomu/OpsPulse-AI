from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit-events", tags=["Audit"])

@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    target_type: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve immutable chronological audit log entries."""
    query = db.query(AuditEvent).filter(
        AuditEvent.organization_id == current_user.organization_id
    )

    if target_type:
        query = query.filter(AuditEvent.target_type == target_type)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)

    offset = (page - 1) * limit
    events = query.order_by(desc(AuditEvent.created_at)).offset(offset).limit(limit).all()
    return events
