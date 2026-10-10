from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import ServiceHealth

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    owner_team: str = "Core Engineering"
    environment: str = "production"
    health_status: ServiceHealth = ServiceHealth.HEALTHY
    escalation_policy_id: Optional[str] = None
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_team: Optional[str] = None
    environment: Optional[str] = None
    health_status: Optional[ServiceHealth] = None
    escalation_policy_id: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: str
    organization_id: str
    slug: str
    escalation_policy_name: Optional[str] = None
    active_incident_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
