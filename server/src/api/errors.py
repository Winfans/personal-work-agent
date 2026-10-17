"""Consistent error responses for JSON API requests."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from src.schemas.response import ApiResponse


JSON_ERROR_RESPONSES = {
    404: {"model": ApiResponse[None], "description": "资源不存在"},
    422: {"model": ApiResponse[None], "description": "请求参数错误"},
    500: {"model": ApiResponse[None], "description": "服务器内部错误"},
    503: {"model": ApiResponse[None], "description": "服务暂不可用"},
}


def _error(status_code: int, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
        headers=headers,
    )


async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return _error(exc.status_code, message, exc.headers)


async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return _error(422, "请求参数错误")


async def server_error(_: Request, __: Exception) -> JSONResponse:
    return _error(500, "服务器内部错误")
