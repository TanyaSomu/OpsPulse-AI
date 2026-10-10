from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import Severity, AlertStatus

class AlertWebhookPayload(BaseModel):
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    severity: Severity = Severity.HIGH
    source: Optional[str] = "Generic Webhook"
    external_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertResponse(BaseModel):
    id: str
    organization_id: str
    service_id: str
    service_name: Optional[str] = None
    incident_id: Optional[str] = None
    external_id: Optional[str] = None
    fingerprint: str
    title: str
    description: Optional[str] = None
    severity: Severity
    source: str
    status: AlertStatus
    payload: Optional[Dict[str, Any]] = None
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertWebhookResponse(BaseModel):
    status: str
    alert: AlertResponse
    incident_id: str
    incident_number: int
    is_new_incident: bool
    deduplicated: bool
