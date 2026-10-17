"""Note API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(default="", max_length=1_000_000)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=1_000_000)

    @model_validator(mode="after")
    def require_change(self) -> "NoteUpdate":
        if self.title is None and self.content is None:
            raise ValueError("title or content is required")
        return self


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
