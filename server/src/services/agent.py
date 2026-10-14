"""Agent orchestration service."""

from collections.abc import AsyncIterator
from typing import Any

from src.config import settings
from src.schemas.agent import AgentRequest
from src.services.chat import ChatService, get_chat_service
from src.services.decision import JevDecisionService
from src.services.rag import BailianRagService, RetrievedChunk


class AgentService:
    """Coordinates model calls, tools, memory, and business workflows."""

    def __init__(
        self,
        chat: ChatService,
        decision: JevDecisionService,
        rag: BailianRagService | None,
    ) -> None:
        self.chat = chat
        self.decision = decision
        self.rag = rag

    async def stream(self, request: AgentRequest) -> AsyncIterator[dict[str, Any]]:
        yield {"type": "start", "model": self.chat.model, "session_id": request.session_id}

        decision = await self.decision.decide(request.latest_user_message())
        yield {
            "type": "route",
            "route": decision.route,
            "confidence": decision.confidence,
            "model": decision.model,
        }

        rag_context: str | None = None
        if decision.route == "rag_chat":
            if self.rag is None:
                raise RuntimeError(
                    "RAG route selected, but BAILIAN_RAG_BASE_URL and "
                    "BAILIAN_RAG_INDEX_ID are not configured"
                )
            chunks = await self.rag.retrieve(request.latest_user_message())
            yield {
                "type": "retrieval",
                "count": len(chunks),
                "sources": _sources(chunks),
            }
            rag_context = _format_rag_context(chunks)

        async for content in self.chat.stream_messages(
            request.conversation(),
            request.temperature,
            rag_context,
        ):
            yield {"type": "delta", "content": content}

        yield {"type": "done"}


def _format_rag_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant knowledge was retrieved."
    return "\n\n".join(
        f"[{index}] Source: {chunk.source or 'unknown'}\n{chunk.content}"
        for index, chunk in enumerate(chunks, start=1)
    )


def _sources(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {"source": chunk.source, "score": chunk.score}
        for chunk in chunks
        if chunk.source or chunk.score is not None
    ]


def get_agent_service() -> AgentService:
    if not settings.typesafe_api_key:
        raise RuntimeError("TYPESAFE_API_KEY is not configured")

    rag = None
    if settings.bailian_rag_base_url and settings.bailian_rag_index_id:
        if not settings.bailian_api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured")
        rag = BailianRagService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_rag_base_url,
            index_id=settings.bailian_rag_index_id,
            top_k=settings.bailian_rag_top_k,
        )

    return AgentService(
        chat=get_chat_service(),
        decision=JevDecisionService(
            api_key=settings.typesafe_api_key,
            base_url=settings.jev_base_url,
            model=settings.jev_model,
            timeout=settings.jev_timeout_seconds,
        ),
        rag=rag,
    )
