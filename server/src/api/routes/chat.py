"""Streamable HTTP text chat endpoint."""

from collections.abc import AsyncIterator
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.schemas.chat import TextChatRequest
from src.services.chat import ChatService, get_chat_service

router = APIRouter()


def _event(event_type: str, **payload: object) -> bytes:
    return (json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n").encode()


def get_configured_chat_service() -> ChatService:
    try:
        return get_chat_service()
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/text", response_class=StreamingResponse)
async def text_chat(
    request: TextChatRequest,
    service: ChatService = Depends(get_configured_chat_service),
) -> StreamingResponse:
    async def stream() -> AsyncIterator[bytes]:
        yield _event("start", model=service.model)
        try:
            async for content in service.stream_text(request):
                yield _event("delta", content=content)
        except Exception as error:
            yield _event("error", message=str(error))
            return
        yield _event("done")

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/text/check", include_in_schema=False)
async def check_chat_configuration() -> dict[str, str]:
    service = get_configured_chat_service()
    return {"status": "ok", "model": service.model}
