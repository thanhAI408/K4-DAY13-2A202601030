from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


REQUEST_ID_PATTERN = re.compile(r"^req-[0-9a-f]{8}$", re.IGNORECASE)


def _new_correlation_id() -> str:
    return f"req-{uuid.uuid4().hex[:8]}"


def _get_correlation_id(request: Request) -> str:
    supplied_id = request.headers.get("x-request-id", "").strip()
    if REQUEST_ID_PATTERN.fullmatch(supplied_id):
        return supplied_id.lower()
    return _new_correlation_id()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()
        correlation_id = _get_correlation_id(request)
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        request.state.request_started_at = start
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = (
                f"{(time.perf_counter() - start) * 1000:.2f}"
            )
            return response
        finally:
            clear_contextvars()
