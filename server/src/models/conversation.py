"""Persisted chat conversations and individual messages."""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_updated_id", "updated_at", "id"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="conversation")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_conversation_id_id", "conversation_id", "id"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
