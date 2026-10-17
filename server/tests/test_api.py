import json
from collections.abc import AsyncIterator

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.routes.agent import get_configured_agent_service
from src.config import settings
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
    assert response.json() == {
        "code": 0,
        "message": "OK",
        "data": {"status": "ok", "environment": settings.environment},
    }


def test_json_errors_use_response_envelope() -> None:
    missing = client.get("/api/v1/missing")
    assert missing.status_code == 404
    assert missing.json() == {"code": 404, "message": "Not Found", "data": None}

    invalid = client.post("/agent/run", json={})
    assert invalid.status_code == 422
    assert invalid.json() == {"code": 422, "message": "请求参数错误", "data": None}


def test_stream_preflight_error_uses_json_envelope() -> None:
    def unavailable() -> None:
        raise HTTPException(status_code=503, detail="Agent service unavailable")

    app.dependency_overrides[get_configured_agent_service] = unavailable
    try:
        response = client.post("/agent/run", json={"message": "hello"})
        assert response.status_code == 503
        assert response.json() == {
            "code": 503,
            "message": "Agent service unavailable",
            "data": None,
        }
    finally:
        app.dependency_overrides.pop(get_configured_agent_service, None)


def test_openapi_documents_validation_envelope() -> None:
    spec = client.get("/openapi.json").json()
    response = spec["paths"]["/api/v1/notes"]["get"]["responses"]["422"]
    schema_ref = response["content"]["application/json"]["schema"]["$ref"]
    schema_name = schema_ref.rsplit("/", 1)[-1]
    assert {"code", "message", "data"} <= set(
        spec["components"]["schemas"][schema_name]["properties"]
    )


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
