"""Top-level API router."""

from fastapi import APIRouter

from src.api.routes import agent, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
