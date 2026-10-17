"""Service health endpoints."""

from fastapi import APIRouter

from src.config import settings
from src.schemas.health import HealthResponse
from src.schemas.response import ApiResponse, success

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthResponse])
async def health() -> ApiResponse[HealthResponse]:
    return success(HealthResponse(status="ok", environment=settings.environment))
