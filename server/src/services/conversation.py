"""Stored chat history operations; no model or HTTP concerns."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_factory
from src.models.conversation import Conversation, ConversationMessage
from src.schemas.chat import ChatMessage


class ConversationService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession] = session_factory) -> None:
        self._sessions = sessions

    async def create(self, title: str) -> Conversation:
        async with self._sessions() as session:
            conversation = Conversation(title=title)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation

    async def list(self, before_id: int | None, limit: int) -> list[Conversation]:
        async with self._sessions() as session:
            query = select(Conversation).order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            if before_id is not None:
                anchor = await session.get(Conversation, before_id)
                if anchor is None:
                    return []
                query = query.where(
                    (Conversation.updated_at < anchor.updated_at)
                    | ((Conversation.updated_at == anchor.updated_at) & (Conversation.id < anchor.id))
                )
            result = await session.scalars(query.limit(limit))
            return list(result.all())

    async def get(self, conversation_id: int) -> Conversation | None:
        async with self._sessions() as session:
            return await session.get(Conversation, conversation_id)

    async def messages(
        self, conversation_id: int, before_id: int | None, limit: int
    ) -> list[ConversationMessage]:
        async with self._sessions() as session:
            query = select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            )
            if before_id is not None:
                query = query.where(ConversationMessage.id < before_id)
            result = await session.scalars(query.order_by(ConversationMessage.id.desc()).limit(limit))
            return list(reversed(result.all()))

    async def append(self, conversation_id: int, role: str, content: str) -> ConversationMessage:
        async with self._sessions() as session:
            conversation = await session.get(Conversation, conversation_id)
            if conversation is None:
                raise ValueError("Conversation not found")
            message = ConversationMessage(
                conversation_id=conversation_id, role=role, content=content
            )
            session.add(message)
            conversation.updated_at = text("CURRENT_TIMESTAMP(6)")
            await session.commit()
            await session.refresh(message)
            return message

    async def recent_context(self, conversation_id: int) -> list[ChatMessage]:
        # AgentRequest is capped at 100 messages, while all messages remain stored.
        messages = await self.messages(conversation_id, None, 100)
        return [ChatMessage(role=message.role, content=message.content) for message in messages]


def get_conversation_service() -> ConversationService:
    return ConversationService()
