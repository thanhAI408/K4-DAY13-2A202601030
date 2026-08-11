from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    return get_client()


def flush_tracing() -> None:
    """Flush queued Langfuse events without making observability fatal."""
    if not tracing_enabled():
        return

    try:
        client = get_langfuse_client()
        flush = getattr(client, "flush", None)
        if callable(flush):
            flush()
    except Exception:  # pragma: no cover - SDK/network dependent
        return


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
