"""Shared envelope for non-streaming JSON API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "OK"
    data: T


def success(data: T) -> ApiResponse[T]:
    return ApiResponse[T](data=data)
