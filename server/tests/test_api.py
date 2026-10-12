from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_agent() -> None:
    response = client.post(
        "/api/v1/agent/run",
        json={"message": "hello", "session_id": "test-session"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Agent received: hello",
        "session_id": "test-session",
    }
