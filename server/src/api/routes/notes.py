"""Note CRUD endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.note import Note
from src.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from src.schemas.response import ApiResponse, success
from src.services.note import NoteService

router = APIRouter()


def get_note_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteService:
    return NoteService(session)


async def _get_note_or_404(note_id: int, service: NoteService) -> Note:
    note = await service.get(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.post("", response_model=ApiResponse[NoteResponse], status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    service: Annotated[NoteService, Depends(get_note_service)],
) -> ApiResponse[NoteResponse]:
    return success(NoteResponse.model_validate(await service.create(payload)))


@router.get("", response_model=ApiResponse[list[NoteResponse]])
async def list_notes(
    service: Annotated[NoteService, Depends(get_note_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[NoteResponse]]:
    notes = await service.list(offset, limit)
    return success([NoteResponse.model_validate(note) for note in notes])


@router.get("/{note_id}", response_model=ApiResponse[NoteResponse])
async def get_note(
    note_id: int,
    service: Annotated[NoteService, Depends(get_note_service)],
) -> ApiResponse[NoteResponse]:
    return success(NoteResponse.model_validate(await _get_note_or_404(note_id, service)))


@router.put("/{note_id}", response_model=ApiResponse[NoteResponse])
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    service: Annotated[NoteService, Depends(get_note_service)],
) -> ApiResponse[NoteResponse]:
    note = await _get_note_or_404(note_id, service)
    return success(NoteResponse.model_validate(await service.update(note, payload)))


@router.delete("/{note_id}", response_model=ApiResponse[None])
async def delete_note(
    note_id: int,
    service: Annotated[NoteService, Depends(get_note_service)],
) -> ApiResponse[None]:
    note = await _get_note_or_404(note_id, service)
    await service.delete(note)
    return success(None)
