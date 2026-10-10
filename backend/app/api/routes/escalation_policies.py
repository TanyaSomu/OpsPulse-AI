from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.escalation import EscalationPolicy, EscalationRule
from app.schemas.escalation import (
    EscalationPolicyCreate, EscalationPolicyUpdate, EscalationPolicyResponse,
    EscalationRuleResponse
)
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/escalation-policies", tags=["Escalation Policies"])

def format_policy_response(policy: EscalationPolicy) -> EscalationPolicyResponse:
    rules = [
        EscalationRuleResponse(
            id=r.id,
            escalation_policy_id=r.escalation_policy_id,
            level_number=r.level_number,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else None,
            user_email=r.user.email if r.user else None,
            created_at=r.created_at
        )
        for r in sorted(policy.rules, key=lambda x: x.level_number)
    ]

    return EscalationPolicyResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        name=policy.name,
        description=policy.description,
        ack_timeout_seconds=policy.ack_timeout_seconds,
        is_active=policy.is_active,
        rules=rules,
        created_at=policy.created_at
    )

@router.get("", response_model=List[EscalationPolicyResponse])
def list_escalation_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all configured escalation policies."""
    policies = db.query(EscalationPolicy).filter(
        EscalationPolicy.organization_id == current_user.organization_id
    ).order_by(EscalationPolicy.name).all()
    return [format_policy_response(p) for p in policies]

@router.post("", response_model=EscalationPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_escalation_policy(
    payload: EscalationPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Configure a new escalation policy with ordered escalation tiers (Admin only)."""
    policy = EscalationPolicy(
        organization_id=current_user.organization_id,
        name=payload.name.strip(),
        description=payload.description,
        ack_timeout_seconds=payload.ack_timeout_seconds,
        is_active=payload.is_active
    )
    db.add(policy)
    db.flush()

    for rule_in in payload.rules:
        target_user = db.query(User).filter(User.id == rule_in.user_id).first()
        if not target_user:
            raise HTTPException(status_code=400, detail=f"User {rule_in.user_id} does not exist.")

        rule = EscalationRule(
            escalation_policy_id=policy.id,
            level_number=rule_in.level_number,
            user_id=rule_in.user_id
        )
        db.add(rule)

    record_audit_event(
        db=db,
        organization_id=current_user.organization_id,
        actor=current_user,
        event_type="POLICY_CREATED",
        target_type="POLICY",
        target_id=policy.id,
        details=f"Escalation policy '{policy.name}' configured with {len(payload.rules)} levels."
    )

    db.commit()
    db.refresh(policy)
    return format_policy_response(policy)

@router.get("/{policy_id}", response_model=EscalationPolicyResponse)
def get_escalation_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific escalation policy."""
    policy = db.query(EscalationPolicy).filter(
        EscalationPolicy.id == policy_id,
        EscalationPolicy.organization_id == current_user.organization_id
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    return format_policy_response(policy)

@router.patch("/{policy_id}", response_model=EscalationPolicyResponse)
def update_escalation_policy(
    policy_id: str,
    payload: EscalationPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update escalation policy timeouts, active status, or tier rules (Admin only)."""
    policy = db.query(EscalationPolicy).filter(
        EscalationPolicy.id == policy_id,
        EscalationPolicy.organization_id == current_user.organization_id
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    if payload.name:
        policy.name = payload.name.strip()
    if payload.description is not None:
        policy.description = payload.description
    if payload.ack_timeout_seconds is not None:
        policy.ack_timeout_seconds = payload.ack_timeout_seconds
    if payload.is_active is not None:
        policy.is_active = payload.is_active

    if payload.rules is not None:
        # Replace existing rules
        db.query(EscalationRule).filter(EscalationRule.escalation_policy_id == policy.id).delete()
        for rule_in in payload.rules:
            rule = EscalationRule(
                escalation_policy_id=policy.id,
                level_number=rule_in.level_number,
                user_id=rule_in.user_id
            )
            db.add(rule)

    record_audit_event(
        db=db,
        organization_id=current_user.organization_id,
        actor=current_user,
        event_type="POLICY_UPDATED",
        target_type="POLICY",
        target_id=policy.id,
        details=f"Escalation policy '{policy.name}' updated."
    )

    db.commit()
    db.refresh(policy)
    return format_policy_response(policy)

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_escalation_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an escalation policy (Admin only)."""
    policy = db.query(EscalationPolicy).filter(
        Esc.id == policy_id if hasattr(EscalationPolicy, 'id') else EscalationPolicy.id == policy_id,
        EscalationPolicy.organization_id == current_user.organization_id
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")

    db.delete(policy)
    db.commit()
    return None
