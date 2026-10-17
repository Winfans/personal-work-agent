"""Contracts for stored chat history."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class StoredMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ConversationRunRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    temperature: float = Field(default=0.6, ge=0, le=2)
