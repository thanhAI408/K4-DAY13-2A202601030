from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

REQUEST_ID_RE = re.compile(r"^req-[0-9a-fA-F]{8}$")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Mỗi request phải bắt đầu bằng context sạch để không rò metadata giữa các request.
        clear_contextvars()

        incoming = request.headers.get("x-request-id", "").strip()
        correlation_id = (
            incoming.lower()
            if REQUEST_ID_RE.fullmatch(incoming)
            else f"req-{uuid.uuid4().hex[:8]}"
        )

        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(elapsed_ms)
            return response
        finally:
            clear_contextvars()
