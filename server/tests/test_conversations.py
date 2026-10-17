"""Stored conversation API tests without MySQL or model providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from src.api.routes.agent import get_configured_agent_service
from src.services.conversation import get_conversation_service
from src.main import app
from src.models.conversation import Conversation, ConversationMessage
from src.schemas.agent import AgentRequest


class FakeConversationService:
    def __init__(self) -> None:
        self.conversations: dict[int, SimpleNamespace] = {}
        self.stored_messages: list[SimpleNamespace] = []
        self.next_conversation_id = 1
        self.next_message_id = 1

    async def create(self, title: str) -> SimpleNamespace:
        now = datetime(2026, 10, 17, 12, 0, 0)
        conversation = SimpleNamespace(
            id=self.next_conversation_id, title=title, created_at=now, updated_at=now
        )
        self.conversations[conversation.id] = conversation
        self.next_conversation_id += 1
        return conversation

    async def list(self, before_id: int | None, limit: int) -> list[SimpleNamespace]:
        ordered = sorted(
            self.conversations.values(), key=lambda item: (item.updated_at, item.id), reverse=True
        )
        if before_id is not None:
            anchor = self.conversations.get(before_id)
            if anchor is None:
                return []
            ordered = [item for item in ordered if
                (item.updated_at, item.id) < (anchor.updated_at, anchor.id)]
        return ordered[:limit]

    async def get(self, conversation_id: int) -> SimpleNamespace | None:
        return self.conversations.get(conversation_id)

    async def messages(
        self, conversation_id: int, before_id: int | None, limit: int
    ) -> list[SimpleNamespace]:
        selected = [message for message in self.stored_messages
            if message.conversation_id == conversation_id
            and (before_id is None or message.id < before_id)]
        return selected[-limit:]

    async def append(self, conversation_id: int, role: str, content: str) -> SimpleNamespace:
        conversation = self.conversations[conversation_id]
        message = SimpleNamespace(
            id=self.next_message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=conversation.created_at + timedelta(seconds=self.next_message_id),
        )
        self.stored_messages.append(message)
        self.next_message_id += 1
        conversation.updated_at = message.created_at
        return message

    async def recent_context(self, conversation_id: int) -> list[dict[str, str]]:
        selected = await self.messages(conversation_id, None, 100)
        return [dict(role=message.role, content=message.content) for message in selected]


class FakeAgent:
    async def stream(self, request: AgentRequest) -> AsyncIterator[dict[str, object]]:
        assert request.session_id is not None
        assert request.latest_user_message()
        yield {"type": "start", "model": "test", "session_id": request.session_id}
        yield {"type": "route", "route": "general_chat", "confidence": 1, "model": "test"}
        yield {"type": "delta", "content": "第一段"}
        yield {"type": "delta", "content": "第二段"}
        yield {"type": "done"}


class FailingAgent:
    async def stream(self, request: AgentRequest) -> AsyncIterator[dict[str, object]]:
        yield {"type": "start", "model": "test", "session_id": request.session_id}
        raise RuntimeError("模型故障")


def test_mysql_conversation_schema_has_history_relationship_and_indexes() -> None:
    conversation_sql = str(CreateTable(Conversation.__table__).compile(dialect=mysql.dialect()))
    message_sql = str(CreateTable(ConversationMessage.__table__).compile(dialect=mysql.dialect()))
    assert "DATETIME(6)" in conversation_sql
    assert "LONGTEXT" in message_sql
    assert "FOREIGN KEY(conversation_id) REFERENCES conversations (id)" in message_sql
    assert "ix_conversations_updated_id" in {
        index.name for index in Conversation.__table__.indexes
    }
    assert "ix_conversation_messages_conversation_id_id" in {
        index.name for index in ConversationMessage.__table__.indexes
    }


def test_multiple_conversations_history_and_persisted_stream() -> None:
    service = FakeConversationService()
    app.dependency_overrides[get_conversation_service] = lambda: service
    app.dependency_overrides[get_configured_agent_service] = FakeAgent
    try:
        client = TestClient(app)
        first = client.post("/api/v1/conversations", json={"title": "第一个"})
        second = client.post("/api/v1/conversations", json={"title": "第二个"})
        assert first.status_code == 201
        assert first.json()["code"] == 0
        assert second.json()["data"]["id"] == 2

        streamed = client.post("/api/v1/conversations/1/run", json={"message": "你好"})
        events = [line for line in streamed.text.splitlines() if line]
        assert [json.loads(line)["type"] for line in events] == [
            "start", "route", "delta", "delta", "done"
        ]
        assert streamed.headers["content-type"].startswith("application/x-ndjson")

        messages = client.get("/api/v1/conversations/1/messages")
        assert messages.json()["data"][0]["content"] == "你好"
        assert messages.json()["data"][1]["content"] == "第一段第二段"
        assert client.get("/api/v1/conversations/2/messages").json()["data"] == []
        assert [item["id"] for item in client.get("/api/v1/conversations").json()["data"]] == [1, 2]
        assert [item["id"] for item in client.get(
            "/api/v1/conversations/1/messages?before_id=2&limit=1"
        ).json()["data"]] == [1]
        assert client.get("/api/v1/conversations/1").json()["data"]["title"] == "第一个"
        assert client.get("/api/v1/conversations/999").status_code == 404
    finally:
        app.dependency_overrides.pop(get_conversation_service, None)
        app.dependency_overrides.pop(get_configured_agent_service, None)


def test_failed_stream_keeps_user_message_without_inventing_assistant_reply() -> None:
    service = FakeConversationService()
    app.dependency_overrides[get_conversation_service] = lambda: service
    app.dependency_overrides[get_configured_agent_service] = FailingAgent
    try:
        client = TestClient(app)
        client.post("/api/v1/conversations", json={"title": "失败测试"})
        response = client.post("/api/v1/conversations/1/run", json={"message": "问题"})
        assert '"type": "error"' in response.text
        assert [message.role for message in service.stored_messages] == ["user"]
    finally:
        app.dependency_overrides.pop(get_conversation_service, None)
        app.dependency_overrides.pop(get_configured_agent_service, None)
