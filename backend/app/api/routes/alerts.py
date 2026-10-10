from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.alert import Alert
from app.models.enums import AlertStatus, Severity
from app.schemas.alert import AlertWebhookPayload, AlertWebhookResponse, AlertResponse
from app.services.alert_service import ingest_webhook_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.post("/webhook", response_model=AlertWebhookResponse, status_code=status.HTTP_201_CREATED)
def receive_webhook_alert(
    payload: AlertWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Public webhook receiver for incoming monitoring system alerts.
    Performs payload validation, fingerprinting, deduplication, and automatic incident correlation.
    """
    return ingest_webhook_alert(db, payload)

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[Severity] = None,
    service_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical alert log with filtering."""
    query = db.query(Alert).filter(Alert.organization_id == current_user.organization_id)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if service_id:
        query = query.filter(Alert.service_id == service_id)

    offset = (page - 1) * limit
    alerts = query.order_by(desc(Alert.received_at)).offset(offset).limit(limit).all()

    return [
        AlertResponse(
            id=a.id,
            organization_id=a.organization_id,
            service_id=a.service_id,
            service_name=a.service.name if a.service else None,
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
        for a in alerts
    ]

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        id=alert.id,
        organization_id=alert.organization_id,
        service_id=alert.service_id,
        service_name=alert.service.name if alert.service else None,
        incident_id=alert.incident_id,
        external_id=alert.external_id,
        fingerprint=alert.fingerprint,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        source=alert.source,
        status=alert.status,
        payload=alert.payload,
        received_at=alert.received_at
    )
