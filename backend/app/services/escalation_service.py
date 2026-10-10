from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.incident import Incident, IncidentEvent, IncidentAssignment
from app.models.escalation import EscalationPolicy, EscalationRule
from app.models.notification import Notification
from app.models.enums import IncidentStatus
from app.services.audit_service import record_audit_event

def check_and_escalate_incidents(db: Session) -> Dict[str, Any]:
    """Check all unacknowledged incidents with expired SLA deadlines and advance escalation."""
    now = datetime.now(timezone.utc)
    expired_incidents = db.query(Incident).filter(
        Incident.status == IncidentStatus.TRIGGERED,
        Incident.ack_deadline != None,
        Incident.ack_deadline <= now
    ).all()

    escalated_count = 0
    exhausted_count = 0
    escalated_ids = []

    for incident in expired_incidents:
        policy = incident.escalation_policy
        if not policy:
            # Fallback to org default active policy if available
            policy = db.query(EscalationPolicy).filter(
                EscalationPolicy.organization_id == incident.organization_id,
                EscalationPolicy.is_active == True
            ).first()

        rules = sorted(policy.rules, key=lambda r: r.level_number) if policy and policy.rules else []
        next_level = incident.current_escalation_level + 1
        next_rule = next((r for r in rules if r.level_number == next_level), None)

        if next_rule and next_rule.user:
            # Advance to next escalation tier
            old_level = incident.current_escalation_level
            incident.current_escalation_level = next_rule.level_number
            incident.assigned_responder_id = next_rule.user_id

            timeout_seconds = policy.ack_timeout_seconds if policy else 300
            incident.ack_deadline = now + timedelta(seconds=timeout_seconds)
            incident.updated_at = now

            db.add(IncidentAssignment(
                incident_id=incident.id,
                user_id=next_rule.user_id,
                assigned_at=now
            ))

            db.add(IncidentEvent(
                incident_id=incident.id,
                event_type="ESCALATED",
                actor_name="OpsPulse Escalation Engine",
                message=f"Incident escalated from Level {old_level} to Level {next_rule.level_number} ({next_rule.user.full_name}). SLA timer reset to {timeout_seconds // 60}m.",
                metadata_json={
                    "previous_level": old_level,
                    "new_level": next_rule.level_number,
                    "responder": next_rule.user.full_name,
                    "responder_id": next_rule.user_id
                }
            ))

            db.add(Notification(
                incident_id=incident.id,
                user_id=next_rule.user_id,
                channel="APP_NOTIFICATION",
                title=f"ESCALATION ALERT #{incident.incident_number}: {incident.title}",
                body=f"Incident escalated to Level {next_rule.level_number}. Immediate action required.",
                status="DELIVERED"
            ))

            record_audit_event(
                db=db,
                organization_id=incident.organization_id,
                event_type="INCIDENT_ESCALATED",
                target_type="INCIDENT",
                target_id=incident.id,
                details=f"Incident #{incident.incident_number} escalated to Level {next_rule.level_number} ({next_rule.user.full_name})."
            )

            escalated_count += 1
            escalated_ids.append(incident.id)

        else:
            # Reached max level or no further rules configured
            incident.ack_deadline = None
            incident.updated_at = now

            db.add(IncidentEvent(
                incident_id=incident.id,
                event_type="ESCALATION_EXHAUSTED",
                actor_name="OpsPulse Escalation Engine",
                message="Escalation policy exhausted. All configured escalation tiers have been notified. Incident remains in breach.",
                metadata_json={"final_level": incident.current_escalation_level}
            ))

            record_audit_event(
                db=db,
                organization_id=incident.organization_id,
                event_type="ESCALATION_EXHAUSTED",
                target_type="INCIDENT",
                target_id=incident.id,
                details=f"Escalation tiers exhausted for incident #{incident.incident_number}."
            )

            exhausted_count += 1

    if expired_incidents:
        db.commit()

    return {
        "checked_at": now.isoformat(),
        "expired_found": len(expired_incidents),
        "escalated_count": escalated_count,
        "exhausted_count": exhausted_count,
        "escalated_incident_ids": escalated_ids
    }
