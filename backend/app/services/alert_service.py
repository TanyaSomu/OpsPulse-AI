import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.service import Service
from app.models.alert import Alert
from app.models.incident import Incident, IncidentEvent
from app.models.escalation import EscalationPolicy, EscalationRule
from app.models.notification import Notification
from app.models.enums import Severity, IncidentStatus, AlertStatus, ServiceHealth
from app.schemas.alert import AlertWebhookPayload, AlertWebhookResponse, AlertResponse
from app.services.audit_service import record_audit_event

def generate_alert_fingerprint(service_id: str, title: str, source: str, external_id: Optional[str] = None) -> str:
    """Generate a deterministic fingerprint hash for deduplication and grouping."""
    if external_id:
        raw_key = f"{service_id}:{external_id.strip()}"
    else:
        normalized_title = title.strip().lower()
        normalized_source = (source or "generic").strip().lower()
        raw_key = f"{service_id}:{normalized_source}:{normalized_title}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]

def find_or_validate_service(db: Session, payload: AlertWebhookPayload) -> Service:
    service = None
    if payload.service_id:
        service = db.query(Service).filter(Service.id == payload.service_id).first()
    elif payload.service_name:
        service = db.query(Service).filter(
            func.lower(Service.name) == payload.service_name.strip().lower()
        ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target service not found. Specify a valid 'service_id' or 'service_name'."
        )
    return service

def ingest_webhook_alert(db: Session, payload: AlertWebhookPayload) -> AlertWebhookResponse:
    now = datetime.now(timezone.utc)
    service = find_or_validate_service(db, payload)

    fingerprint = generate_alert_fingerprint(
        service_id=service.id,
        title=payload.title,
        source=payload.source or "Generic Webhook",
        external_id=payload.external_id
    )

    correlation_threshold = now - timedelta(minutes=settings.ALERT_CORRELATION_WINDOW_MINUTES)

    # Check for active incident for this service and fingerprint within the correlation window
    active_incident = db.query(Incident).filter(
        Incident.service_id == service.id,
        Incident.fingerprint == fingerprint,
        Incident.status.in_([IncidentStatus.TRIGGERED, IncidentStatus.ACKNOWLEDGED]),
        Incident.updated_at >= correlation_threshold
    ).first()

    is_new_incident = False
    is_deduplicated = False

    if active_incident:
        # Correlate and deduplicate alert into existing incident
        is_deduplicated = True
        active_incident.alert_count += 1
        active_incident.updated_at = now

        # If incoming alert has higher severity, elevate incident
        severity_rank = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }
        if severity_rank.get(payload.severity, 0) > severity_rank.get(active_incident.severity, 0):
            old_sev = active_incident.severity
            active_incident.severity = payload.severity
            db.add(IncidentEvent(
                incident_id=active_incident.id,
                event_type="SEVERITY_CHANGED",
                actor_name="OpsPulse Correlation Engine",
                message=f"Incident severity elevated from {old_sev.value} to {payload.severity.value} due to correlated critical alert.",
                metadata_json={"alert_title": payload.title, "new_severity": payload.severity.value}
            ))

        alert = Alert(
            organization_id=service.organization_id,
            service_id=service.id,
            incident_id=active_incident.id,
            external_id=payload.external_id,
            fingerprint=fingerprint,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            source=payload.source or "Generic Webhook",
            status=AlertStatus.DEDUPLICATED,
            payload=payload.metadata or {},
            received_at=payload.timestamp or now
        )
        db.add(alert)
        db.flush()

        # Add event to incident timeline
        db.add(IncidentEvent(
            incident_id=active_incident.id,
            event_type="ALERT_GROUPED",
            actor_name="OpsPulse Deduplication Engine",
            message=f"Grouped correlated alert '{payload.title}' (Fingerprint: {fingerprint[:8]}...) into existing incident #{active_incident.incident_number}.",
            metadata_json={"alert_id": alert.id, "source": alert.source, "external_id": alert.external_id}
        ))

        incident = active_incident

    else:
        # Create new incident
        is_new_incident = True

        # Find escalation policy
        policy = None
        if service.escalation_policy_id:
            policy = db.query(EscalationPolicy).filter(
                EscalationPolicy.id == service.escalation_policy_id,
                EscalationPolicy.is_active == True
            ).first()

        if not policy:
            policy = db.query(EscalationPolicy).filter(
                EscalationPolicy.organization_id == service.organization_id,
                EscalationPolicy.is_active == True
            ).first()

        timeout_seconds = policy.ack_timeout_seconds if policy else settings.DEFAULT_ACK_TIMEOUT_SECONDS
        ack_deadline = now + timedelta(seconds=timeout_seconds)

        # Level 1 responder
        assigned_user_id = None
        if policy and policy.rules:
            # First rule (level 1)
            level_1_rule = min(policy.rules, key=lambda r: r.level_number)
            assigned_user_id = level_1_rule.user_id

        # Calculate next incident number
        max_num = db.query(func.max(Incident.incident_number)).scalar() or 1000
        incident_number = max_num + 1

        incident = Incident(
            incident_number=incident_number,
            organization_id=service.organization_id,
            service_id=service.id,
            title=payload.title,
            description=payload.description or f"Triggered by alert '{payload.title}' from {payload.source}",
            severity=payload.severity,
            status=IncidentStatus.TRIGGERED,
            assigned_responder_id=assigned_user_id,
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

        alert = Alert(
            organization_id=service.organization_id,
            service_id=service.id,
            incident_id=incident.id,
            external_id=payload.external_id,
            fingerprint=fingerprint,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            source=payload.source or "Generic Webhook",
            status=AlertStatus.PROCESSED,
            payload=payload.metadata or {},
            received_at=payload.timestamp or now
        )
        db.add(alert)
        db.flush()

        # Update service health
        if payload.severity in [Severity.CRITICAL, Severity.HIGH]:
            service.health_status = ServiceHealth.FAILING
        else:
            if service.health_status == ServiceHealth.HEALTHY:
                service.health_status = ServiceHealth.DEGRADED

        # Record timeline event
        db.add(IncidentEvent(
            incident_id=incident.id,
            event_type="TRIGGERED",
            actor_name="OpsPulse Alert Engine",
            message=f"Incident #{incident.incident_number} triggered by incoming alert '{payload.title}' from {payload.source}.",
            metadata_json={"alert_id": alert.id, "severity": payload.severity.value, "deadline_seconds": timeout_seconds}
        ))

        # Notification for responder
        if assigned_user_id:
            db.add(Notification(
                incident_id=incident.id,
                user_id=assigned_user_id,
                channel="APP_NOTIFICATION",
                title=f"New Incident #{incident.incident_number}: {incident.title}",
                body=f"High severity incident triggered on service {service.name}. Acknowledgement deadline in {timeout_seconds // 60}m.",
                status="DELIVERED"
            ))

    record_audit_event(
        db=db,
        organization_id=service.organization_id,
        event_type="ALERT_INGESTED",
        target_type="ALERT",
        details=f"Alert '{alert.title}' ingested. Fingerprint: {fingerprint[:8]}..., Status: {alert.status.value}, Incident: #{incident.incident_number}",
        target_id=alert.id
    )

    db.commit()
    db.refresh(alert)
    db.refresh(incident)

    alert_resp = AlertResponse(
        id=alert.id,
        organization_id=alert.organization_id,
        service_id=alert.service_id,
        service_name=service.name,
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

    return AlertWebhookResponse(
        status="success",
        alert=alert_resp,
        incident_id=incident.id,
        incident_number=incident.incident_number,
        is_new_incident=is_new_incident,
        deduplicated=is_deduplicated
    )
