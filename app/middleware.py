from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear contextvars to avoid leakage between requests.
        clear_contextvars()

        # Reuse a well-formed upstream request ID or generate req-<8-char-hex>.
        incoming_id = request.headers.get("x-request-id")
        if incoming_id and re.fullmatch(r"req-[0-9a-fA-F]{8}", incoming_id):
            correlation_id = incoming_id.lower()
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # Make the ID available to every structlog event in this request.
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)

            # Return correlation and timing metadata to the caller.
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(
                int((time.perf_counter() - start) * 1000)
            )

            return response
        finally:
            clear_contextvars()
