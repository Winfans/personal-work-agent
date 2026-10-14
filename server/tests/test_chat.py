import json
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from src.api.routes.agent import get_configured_agent_service
from src.main import app
from src.schemas.agent import AgentRequest


class FakeAgentService:
    async def stream(self, _: AgentRequest) -> AsyncIterator[dict[str, object]]:
        yield {"type": "start", "model": "test-model", "session_id": None}
        yield {"type": "route", "route": "general_chat", "confidence": 0.9}
        yield {"type": "delta", "content": "你好"}
        yield {"type": "delta", "content": "，世界"}
        yield {"type": "done"}


def override_agent_service() -> FakeAgentService:
    return FakeAgentService()


client = TestClient(app)


def test_text_chat_stream() -> None:
    app.dependency_overrides[get_configured_agent_service] = override_agent_service
    response = client.post(
        "/chat/text",
        json={"messages": [{"role": "user", "content": "你好"}]},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")

    events = [json.loads(line) for line in response.text.splitlines()]
    assert events == [
        {"type": "start", "model": "test-model", "session_id": None},
        {"type": "route", "route": "general_chat", "confidence": 0.9},
        {"type": "delta", "content": "你好"},
        {"type": "delta", "content": "，世界"},
        {"type": "done"},
    ]
    app.dependency_overrides.pop(get_configured_agent_service, None)
