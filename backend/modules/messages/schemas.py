from typing import Optional
from pydantic import BaseModel, Field


class AttachmentInfo(BaseModel):
    filename: str
    url: str
    content_type: str = "application/octet-stream"
    size: int = 0


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    reply_to_message_id: Optional[str] = None
    attachments: list[AttachmentInfo] = []


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
