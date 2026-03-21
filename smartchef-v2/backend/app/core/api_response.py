"""T019: Unified response envelope (ad-global.md §4 + dd-global.md §2)."""

import math
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def success_response(data: Any = None, *, msg: str = "success", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": "000000", "data": data, "msg": msg},
    )


def error_response(code: str, msg: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "data": None, "msg": msg},
    )


def paginated_response(
    items: list[Any],
    *,
    total: int,
    page: int,
    page_size: int,
    status_code: int = 200,
    total_zh: int | None = None,
    total_en: int | None = None,
) -> JSONResponse:
    pages = math.ceil(total / page_size) if page_size > 0 else 0
    data: dict[str, Any] = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
    if total_zh is not None:
        data["total_zh"] = total_zh
    if total_en is not None:
        data["total_en"] = total_en
    return JSONResponse(
        status_code=status_code,
        content={"code": "000000", "data": data, "msg": "success"},
    )


class BusinessException(HTTPException):
    """Domain-level business error with structured error code."""

    def __init__(self, code: str, msg: str, *, http_status: int = 400):
        self.error_code = code
        self.error_msg = msg
        super().__init__(status_code=http_status, detail=msg)


class AuthException(BusinessException):
    """Authentication / authorization error."""

    pass


async def business_exception_handler(_request: Request, exc: BusinessException) -> JSONResponse:
    return error_response(exc.error_code, exc.error_msg, exc.status_code)
