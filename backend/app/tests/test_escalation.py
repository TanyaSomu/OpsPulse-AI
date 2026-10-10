from datetime import datetime, timezone, timedelta
from app.models.incident import Incident
from app.models.service import Service
from app.models.enums import IncidentStatus, Severity
from app.services.escalation_service import check_and_escalate_incidents

def test_escalation_advances_level_on_expired_deadline(db_session):
    service = db_session.query(Service).filter(Service.name == "Order Processing Pipeline").first()

    # Create an unacknowledged incident with expired deadline
    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_number=9999,
        organization_id=service.organization_id,
        service_id=service.id,
        title="Simulated SLA breach test",
        severity=Severity.HIGH,
        status=IncidentStatus.TRIGGERED,
        escalation_policy_id=service.escalation_policy_id,
        current_escalation_level=1,
        ack_deadline=now - timedelta(minutes=5),  # already expired
        fingerprint="test-sla-breach-fingerprint",
        created_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=5)
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    # Run escalation check
    result = check_and_escalate_incidents(db_session)
    assert result["escalated_count"] >= 1
    assert incident.id in result["escalated_incident_ids"]

    # Verify incident advanced to level 2
    db_session.refresh(incident)
    assert incident.current_escalation_level == 2
    assert incident.ack_deadline > now  # new deadline reset

    # Clean up test incident
    db_session.delete(incident)
    db_session.commit()
