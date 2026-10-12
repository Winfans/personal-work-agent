"""Agent endpoint schemas."""

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    session_id: str | None = None


class AgentResponse(BaseModel):
    reply: str
    session_id: str | None = None
