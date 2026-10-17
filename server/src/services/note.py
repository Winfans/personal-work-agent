"""Note CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.note import Note
from src.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, offset: int, limit: int) -> list[Note]:
        result = await self._session.scalars(
            select(Note)
            .order_by(Note.updated_at.desc(), Note.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def get(self, note_id: int) -> Note | None:
        return await self._session.get(Note, note_id)

    async def create(self, payload: NoteCreate) -> Note:
        note = Note(title=payload.title, content=payload.content)
        self._session.add(note)
        await self._session.commit()
        await self._session.refresh(note)
        return note

    async def update(self, note: Note, payload: NoteUpdate) -> Note:
        if payload.title is not None:
            note.title = payload.title
        if payload.content is not None:
            note.content = payload.content
        await self._session.commit()
        await self._session.refresh(note)
        return note

    async def delete(self, note: Note) -> None:
        await self._session.delete(note)
        await self._session.commit()
