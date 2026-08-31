from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from aeo_shared.errors import ERROR_MESSAGES, ErrorCode

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Unified API response per docs/04_ARCHITECTURE_STANDARDS.md §5.2."""

    code: int = Field(default=0, description="0 = success")
    message: str = Field(default="ok")
    data: T | None = None
    request_id: str = Field(default="")


def success_response(data: T, request_id: str) -> ApiResponse[T]:
    return ApiResponse(code=0, message="ok", data=data, request_id=request_id)


def error_response(
    code: ErrorCode, request_id: str, message: str | None = None
) -> ApiResponse[None]:
    return ApiResponse(
        code=int(code),
        message=message or ERROR_MESSAGES.get(code, "error"),
        data=None,
        request_id=request_id,
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Pagination per docs/04_ARCHITECTURE_STANDARDS.md §5.4."""

    items: list[T]
    total: int
    page: int
    page_size: int
