"""Streamable HTTP agent execution endpoint."""

from collections.abc import AsyncIterator
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.schemas.agent import AgentRequest
from src.services.agent import AgentService, get_agent_service

router = APIRouter()


def _event(event: dict[str, object]) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode()


def get_configured_agent_service() -> AgentService:
    try:
        return get_agent_service()
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/run", response_class=StreamingResponse)
async def run_agent(
    request: AgentRequest,
    service: AgentService = Depends(get_configured_agent_service),
) -> StreamingResponse:
    async def stream() -> AsyncIterator[bytes]:
        try:
            async for event in service.stream(request):
                yield _event(event)
        except Exception as error:
            yield _event({"type": "error", "message": str(error)})

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
