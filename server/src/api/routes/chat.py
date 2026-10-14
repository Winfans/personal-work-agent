"""Streamable HTTP text chat endpoint."""

from collections.abc import AsyncIterator
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.schemas.chat import TextChatRequest
from src.schemas.agent import AgentRequest
from src.services.agent import AgentService
from src.api.routes.agent import get_configured_agent_service

router = APIRouter()


def _event(event_type: str, **payload: object) -> bytes:
    return (json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n").encode()


@router.post("/text", response_class=StreamingResponse)
async def text_chat(
    request: TextChatRequest,
    service: AgentService = Depends(get_configured_agent_service),
) -> StreamingResponse:
    async def stream() -> AsyncIterator[bytes]:
        try:
            agent_request = AgentRequest(
                messages=request.messages,
                temperature=request.temperature,
            )
            async for event in service.stream(agent_request):
                yield (json.dumps(event, ensure_ascii=False) + "\n").encode()
        except Exception as error:
            yield _event("error", message=str(error))

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
