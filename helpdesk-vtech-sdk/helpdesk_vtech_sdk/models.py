from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Attachment(BaseModel):
    filename: str
    url: str
    content_type: str = "application/octet-stream"
    size: int = 0


class ReplyPreview(BaseModel):
    id: str
    sender_username: str
    content: str


class Message(BaseModel):
    id: str
    ticket_id: str
    sender_id: str
    sender_username: str
    sender_role: str
    content: str
    attachments: list[Attachment] = []
    reply_to_message_id: Optional[str] = None
    reply_preview: Optional[ReplyPreview] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime


class SlaBlock(BaseModel):
    first_response_due_at: Optional[datetime] = None
    resolve_due_at: Optional[datetime] = None
    first_responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    first_response_breached: bool = False
    resolve_breached: bool = False
    first_response_near_breach: bool = False
    resolve_near_breach: bool = False


class LockBlock(BaseModel):
    locked_by: Optional[str] = None
    locked_by_username: Optional[str] = None
    locked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class Ticket(BaseModel):
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
    lock: Optional[LockBlock] = None
    resolution_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EscalationRequest(BaseModel):
    id: str
    type: str
    ticket_id: str
    requested_by: str
    requested_by_username: str
    reason: str
    target_technician_id: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
