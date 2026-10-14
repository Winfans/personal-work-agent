"""Agent endpoint schemas."""

from pydantic import BaseModel, Field, model_validator

from src.schemas.chat import ChatMessage


class AgentRequest(BaseModel):
    messages: list[ChatMessage] | None = Field(default=None, min_length=1, max_length=100)
    message: str | None = Field(default=None, min_length=1, max_length=20_000)
    session_id: str | None = None
    temperature: float = Field(default=0.6, ge=0, le=2)

    @model_validator(mode="after")
    def require_message_input(self) -> "AgentRequest":
        if not self.messages and not self.message:
            raise ValueError("messages or message is required")
        return self

    def conversation(self) -> list[ChatMessage]:
        if self.messages:
            return self.messages
        return [ChatMessage(role="user", content=self.message or "")]

    def latest_user_message(self) -> str:
        for message in reversed(self.conversation()):
            if message.role == "user":
                return message.content
        raise ValueError("at least one user message is required")


class AgentResponse(BaseModel):
    reply: str
    session_id: str | None = None
