"""Conversation history and persisted streaming chat."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from src.api.routes.agent import _event, get_configured_agent_service
from src.schemas.agent import AgentRequest
from src.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationRunRequest,
    StoredMessageResponse,
)
from src.schemas.response import ApiResponse, success
from src.services.agent import AgentService
from src.services.conversation import ConversationService, get_conversation_service

router = APIRouter()


@router.post("", response_model=ApiResponse[ConversationResponse], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ApiResponse[ConversationResponse]:
    return success(ConversationResponse.model_validate(await service.create(payload.title)))


@router.get("", response_model=ApiResponse[list[ConversationResponse]])
async def list_conversations(
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    before_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> ApiResponse[list[ConversationResponse]]:
    conversations = await service.list(before_id, limit)
    return success([ConversationResponse.model_validate(item) for item in conversations])


async def _get_or_404(conversation_id: int, service: ConversationService) -> ConversationResponse:
    conversation = await service.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ApiResponse[ConversationResponse])
async def get_conversation(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ApiResponse[ConversationResponse]:
    return success(await _get_or_404(conversation_id, service))


@router.get("/{conversation_id}/messages", response_model=ApiResponse[list[StoredMessageResponse]])
async def list_messages(
    conversation_id: int,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    before_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[list[StoredMessageResponse]]:
    await _get_or_404(conversation_id, service)
    messages = await service.messages(conversation_id, before_id, limit)
    return success([StoredMessageResponse.model_validate(item) for item in messages])


@router.post("/{conversation_id}/run", response_class=StreamingResponse)
async def run_conversation(
    conversation_id: int,
    payload: ConversationRunRequest,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    agent: Annotated[AgentService, Depends(get_configured_agent_service)],
) -> StreamingResponse:
    await _get_or_404(conversation_id, service)

    async def stream() -> AsyncIterator[bytes]:
        try:
            await service.append(conversation_id, "user", payload.message)
            request = AgentRequest(
                messages=await service.recent_context(conversation_id),
                session_id=str(conversation_id),
                temperature=payload.temperature,
            )
            reply_parts: list[str] = []
            async for event in agent.stream(request):
                if event["type"] == "delta":
                    reply_parts.append(str(event.get("content", "")))
                if event["type"] == "done" and reply_parts:
                    await service.append(conversation_id, "assistant", "".join(reply_parts))
                yield _event(event)
        except Exception as error:
            yield _event({"type": "error", "message": str(error)})

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
