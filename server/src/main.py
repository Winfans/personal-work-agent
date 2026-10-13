"""FastAPI application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.api.routes.chat import router as chat_router
from src.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Initialize shared model clients, databases, or tool registries here.
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["null", "http://localhost", "http://127.0.0.1"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(api_router, prefix="/api/v1")
    application.include_router(chat_router, prefix="/chat", tags=["chat"])
    return application


app = create_app()
