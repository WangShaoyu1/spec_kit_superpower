"""T020: Input validation middleware (ad-global.md §6.1)."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings


class InputValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.INPUT_MAX_LENGTH * 10:
                return JSONResponse(
                    status_code=413,
                    content={"code": "E00005", "data": None, "msg": "请求体过大"},
                )

        response = await call_next(request)
        return response
