from typing import Optional
from pydantic import BaseModel, Field


class SubmitCsatRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)
