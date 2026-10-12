"""Service health endpoints."""

from fastapi import APIRouter

from src.config import settings
from src.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
