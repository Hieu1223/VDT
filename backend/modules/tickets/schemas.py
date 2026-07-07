from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateTicketRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=5000)
    category: str = Field(min_length=1, max_length=60)
    impact: str = Field(description="high, medium, or low")
    urgency: str = Field(description="high, medium, or low")


class ResolveTicketRequest(BaseModel):
    resolution_note: str = Field(min_length=3, max_length=3000)


class RejectTicketRequest(BaseModel):
    rejection_reason: str = Field(min_length=3, max_length=1000)


class SlaBlock(BaseModel):
    first_response_due_at: Optional[datetime] = None
    resolve_due_at: Optional[datetime] = None
    first_responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    first_response_breached: bool = False
    resolve_breached: bool = False
    first_response_near_breach: bool = False
    resolve_near_breach: bool = False


class TicketPublic(BaseModel):
    id: str
    subject: str
    description: str
    category: str
    impact: str
    urgency: str
    priority: str
    status: str
    requester_id: str
    requester_username: str
    assignee_id: Optional[str] = None
    assignee_username: Optional[str] = None
    tags: list[str] = []
    sla: Optional[SlaBlock] = None
    lock: Optional[dict] = None
    resolution_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UpdateSlaPolicyRequest(BaseModel):
    first_response_minutes: int = Field(gt=0)
    resolve_minutes: int = Field(gt=0)


class UpdatePriorityMatrixRequest(BaseModel):
    priority: str = Field(description="P1, P2, P3, or P4")
