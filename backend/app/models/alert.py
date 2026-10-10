import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import Severity, AlertStatus

class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_fingerprint_received", "fingerprint", "received_at"),
        Index("ix_alerts_service_status", "service_id", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(Severity), default=Severity.HIGH, nullable=False, index=True)
    source = Column(String(100), default="Generic Webhook", nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.RECEIVED, nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    organization = relationship("Organization", back_populates="alerts")
    service = relationship("Service", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")
