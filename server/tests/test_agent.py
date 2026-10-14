from collections.abc import AsyncIterator

import pytest

from src.schemas.agent import AgentRequest
from src.schemas.chat import ChatMessage
from src.services.agent import AgentService
from src.services.decision import RouteDecision
from src.services.rag import RetrievedChunk


class FakeDecision:
    def __init__(self, route: str) -> None:
        self.route = route

    async def decide(self, _: str) -> RouteDecision:
        return RouteDecision(route=self.route, confidence=0.95, model="jev-test")  # type: ignore[arg-type]


class FakeChat:
    model = "deepseek-test"

    async def stream_messages(
        self,
        _: list[ChatMessage],
        __: float,
        rag_context: str | None = None,
    ) -> AsyncIterator[str]:
        yield "with-rag" if rag_context else "plain"


class FakeRag:
    async def retrieve(self, _: str) -> list[RetrievedChunk]:
        return [RetrievedChunk(content="internal answer", score=0.9, source="handbook.pdf")]


@pytest.mark.asyncio
async def test_general_chat_route_skips_retrieval() -> None:
    service = AgentService(FakeChat(), FakeDecision("general_chat"), None)  # type: ignore[arg-type]
    events = [event async for event in service.stream(AgentRequest(message="hello"))]

    assert [event["type"] for event in events] == ["start", "route", "delta", "done"]
    assert events[2]["content"] == "plain"


@pytest.mark.asyncio
async def test_rag_route_retrieves_before_generation() -> None:
    service = AgentService(FakeChat(), FakeDecision("rag_chat"), FakeRag())  # type: ignore[arg-type]
    events = [event async for event in service.stream(AgentRequest(message="internal policy?"))]

    assert [event["type"] for event in events] == [
        "start",
        "route",
        "retrieval",
        "delta",
        "done",
    ]
    assert events[2]["count"] == 1
    assert events[3]["content"] == "with-rag"
