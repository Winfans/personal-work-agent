"""Top-level API router."""

from fastapi import APIRouter

from src.api.routes import agent, conversations, health, notes

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
