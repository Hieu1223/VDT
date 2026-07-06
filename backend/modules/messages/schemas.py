from typing import Optional
from pydantic import BaseModel, Field, model_validator


class AttachmentInfo(BaseModel):
    filename: str
    url: str
    content_type: str = "application/octet-stream"
    size: int = 0


class SendMessageRequest(BaseModel):
    content: str = Field(default="", max_length=5000)
    reply_to_message_id: Optional[str] = None
    attachments: list[AttachmentInfo] = []

    @model_validator(mode="after")
    def require_content_or_attachment(self) -> "SendMessageRequest":
        if not self.content.strip() and not self.attachments:
            raise ValueError("A message needs text content or at least one attachment")
        return self


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
