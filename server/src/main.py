"""FastAPI application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from src.api.errors import JSON_ERROR_RESPONSES, http_error, server_error, validation_error
from src.api.router import api_router
from src.api.routes.chat import router as chat_router
from src.api.routes.agent import router as agent_router
from src.config import settings
from src.database import bootstrap_database, close_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await bootstrap_database()
    try:
        yield
    finally:
        await close_database()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_exception_handler(HTTPException, http_error)
    application.add_exception_handler(RequestValidationError, validation_error)
    application.add_exception_handler(Exception, server_error)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "null",
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(
        api_router, prefix="/api/v1", responses=JSON_ERROR_RESPONSES
    )
    application.include_router(
        agent_router, prefix="/agent", tags=["agent"], responses=JSON_ERROR_RESPONSES
    )
    application.include_router(
        chat_router, prefix="/chat", tags=["chat"], responses=JSON_ERROR_RESPONSES
    )
    return application


app = create_app()
