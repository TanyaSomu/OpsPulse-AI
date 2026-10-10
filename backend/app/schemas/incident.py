from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import Severity, IncidentStatus
from app.schemas.alert import AlertResponse

class IncidentCreate(BaseModel):
    service_id: str
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    severity: Severity = Severity.HIGH
    assigned_responder_id: Optional[str] = None
    escalation_policy_id: Optional[str] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[Severity] = None
    assigned_responder_id: Optional[str] = None
    escalation_policy_id: Optional[str] = None

class IncidentAssignRequest(BaseModel):
    user_id: str

class IncidentNoteCreate(BaseModel):
    message: str = Field(..., min_length=1)

class IncidentEventResponse(BaseModel):
    id: str
    incident_id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_name: str
    message: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentUpdateResponse(BaseModel):
    id: str
    incident_id: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentResponse(BaseModel):
    id: str
    incident_number: int
    organization_id: str
    service_id: str
    service_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: Severity
    status: IncidentStatus
    assigned_responder_id: Optional[str] = None
    assigned_responder_name: Optional[str] = None
    escalation_policy_id: Optional[str] = None
    escalation_policy_name: Optional[str] = None
    current_escalation_level: int = 1
    ack_deadline: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    mitigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    alert_count: int = 1
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentDetailResponse(IncidentResponse):
    events: List[IncidentEventResponse] = []
    alerts: List[AlertResponse] = []
    updates: List[IncidentUpdateResponse] = []
