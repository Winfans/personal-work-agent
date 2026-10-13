import json
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from src.api.routes.chat import get_configured_chat_service
from src.main import app
from src.schemas.chat import TextChatRequest


class FakeChatService:
    model = "test-model"

    async def stream_text(self, _: TextChatRequest) -> AsyncIterator[str]:
        yield "你好"
        yield "，世界"


def override_chat_service() -> FakeChatService:
    return FakeChatService()


app.dependency_overrides[get_configured_chat_service] = override_chat_service
client = TestClient(app)


def test_text_chat_stream() -> None:
    response = client.post(
        "/chat/text",
        json={"messages": [{"role": "user", "content": "你好"}]},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")

    events = [json.loads(line) for line in response.text.splitlines()]
    assert events == [
        {"type": "start", "model": "test-model"},
        {"type": "delta", "content": "你好"},
        {"type": "delta", "content": "，世界"},
        {"type": "done"},
    ]
