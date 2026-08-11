from __future__ import annotations

import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest
from structlog.contextvars import get_contextvars

from app.main import unhandled_exception_handler
from app.middleware import CorrelationIdMiddleware


def build_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/context")
    async def context(request: Request) -> dict[str, str | None]:
        return {
            "state_id": request.state.correlation_id,
            "context_id": get_contextvars().get("correlation_id"),
        }

    return test_app


def test_middleware_generates_and_propagates_correlation_id() -> None:
    with TestClient(build_test_app()) as client:
        response = client.get("/context")

    correlation_id = response.headers["x-request-id"]
    assert response.status_code == 200
    assert correlation_id == response.json()["state_id"]
    assert correlation_id == response.json()["context_id"]
    assert correlation_id.startswith("req-")
    assert len(correlation_id) == 12
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_middleware_accepts_valid_request_id_and_replaces_invalid_id() -> None:
    with TestClient(build_test_app()) as client:
        valid = client.get("/context", headers={"x-request-id": "REQ-ABCDEF12"})
        invalid = client.get("/context", headers={"x-request-id": "external-id"})

    assert valid.headers["x-request-id"] == "req-abcdef12"
    assert invalid.headers["x-request-id"] != "external-id"
    assert invalid.headers["x-request-id"].startswith("req-")


def test_unhandled_exception_handler_returns_safe_correlated_response() -> None:
    request = StarletteRequest(
        {
            "type": "http",
            "method": "GET",
            "path": "/failure",
            "headers": [],
            "query_string": b"",
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )
    request.state.correlation_id = "req-deadbeef"

    response = asyncio.run(
        unhandled_exception_handler(request, RuntimeError("private detail"))
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.headers["x-request-id"] == "req-deadbeef"
    assert response.body == (
        b'{"detail":"Internal server error","correlation_id":"req-deadbeef"}'
    )
