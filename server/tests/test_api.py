import json
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from src.api.routes.agent import get_configured_agent_service
from src.main import app
from src.schemas.agent import AgentRequest


class FakeAgentService:
    async def stream(self, request: AgentRequest) -> AsyncIterator[dict[str, object]]:
        yield {"type": "start", "model": "test-model", "session_id": request.session_id}
        yield {"type": "route", "route": "general_chat", "confidence": 0.98}
        yield {"type": "delta", "content": "hello"}
        yield {"type": "done"}


def override_agent_service() -> FakeAgentService:
    return FakeAgentService()


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_agent() -> None:
    app.dependency_overrides[get_configured_agent_service] = override_agent_service
    response = client.post(
        "/agent/run",
        json={"message": "hello", "session_id": "test-session"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert [json.loads(line) for line in response.text.splitlines()] == [
        {"type": "start", "model": "test-model", "session_id": "test-session"},
        {"type": "route", "route": "general_chat", "confidence": 0.98},
        {"type": "delta", "content": "hello"},
        {"type": "done"},
    ]
    app.dependency_overrides.pop(get_configured_agent_service, None)
