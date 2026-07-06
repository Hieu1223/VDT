from typing import Optional
from pydantic import BaseModel, Field


class CreateEscalationRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
    suggested_target_id: Optional[str] = None


class CreateReassignmentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
    target_technician_id: str


class ReviewRequestPayload(BaseModel):
    target_technician_id: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=1000)
