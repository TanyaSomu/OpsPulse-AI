from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AuditEventResponse(BaseModel):
    id: str
    organization_id: str
    actor_id: Optional[str] = None
    actor_email: str
    event_type: str
    target_type: str
    target_id: Optional[str] = None
    details: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
