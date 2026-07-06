from typing import List
from pydantic import BaseModel, Field


class UpdateBusinessCalendarRequest(BaseModel):
    business_days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    start_hour: int = Field(ge=0, le=23)
    start_minute: int = Field(ge=0, le=59)
    end_hour: int = Field(ge=0, le=23)
    end_minute: int = Field(ge=0, le=59)
    holidays: List[str] = Field(default_factory=list)
