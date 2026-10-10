from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class EscalationRuleBase(BaseModel):
    level_number: int = Field(ge=1)
    user_id: str

class EscalationRuleCreate(EscalationRuleBase):
    pass

class EscalationRuleResponse(EscalationRuleBase):
    id: str
    escalation_policy_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EscalationPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    ack_timeout_seconds: int = Field(default=300, ge=10)
    is_active: bool = True

class EscalationPolicyCreate(EscalationPolicyBase):
    rules: List[EscalationRuleCreate] = []

class EscalationPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ack_timeout_seconds: Optional[int] = Field(default=None, ge=10)
    is_active: Optional[bool] = None
    rules: Optional[List[EscalationRuleCreate]] = None

class EscalationPolicyResponse(EscalationPolicyBase):
    id: str
    organization_id: str
    rules: List[EscalationRuleResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
