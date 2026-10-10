import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ack_timeout_seconds = Column(Integer, default=300, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="escalation_policies")
    rules = relationship("EscalationRule", back_populates="policy", order_by="EscalationRule.level_number", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="escalation_policy")
    incidents = relationship("Incident", back_populates="escalation_policy")

class EscalationRule(Base):
    __tablename__ = "escalation_rules"
    __table_args__ = (
        UniqueConstraint("escalation_policy_id", "level_number", name="uq_policy_level"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    escalation_policy_id = Column(String(36), ForeignKey("escalation_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    level_number = Column(Integer, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    policy = relationship("EscalationPolicy", back_populates="rules")
    user = relationship("User", back_populates="escalation_rules")
