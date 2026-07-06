from pydantic import BaseModel, Field


class CreateTagRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    color: str = Field(default="#003BFF", max_length=20)


class AttachTagRequest(BaseModel):
    tag: str = Field(min_length=1, max_length=40)
