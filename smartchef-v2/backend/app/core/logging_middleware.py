"""T021: Logging middleware — structured request/response logging (dd-monitoring.md §4.1)."""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("smartchef.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "[%s] %s %s → 500 (%.1fms)",
                request_id, method, path, elapsed,
            )
            raise

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "[%s] %s %s → %d (%.1fms)",
            request_id, method, path, response.status_code, elapsed,
        )

        response.headers["X-Request-ID"] = request_id
        return response
