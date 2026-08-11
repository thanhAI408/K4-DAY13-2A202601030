from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest
from structlog.contextvars import get_contextvars

from app import logging_config
from app.main import app, unhandled_exception_handler
from app.middleware import CorrelationIdMiddleware
from app.pii import hash_user_id


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


def test_chat_logs_include_request_context(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "req-1234abcd"},
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    api_events = [event for event in events if event.get("service") == "api"]
    expected_context = {
        "correlation_id": "req-1234abcd",
        "user_id_hash": hash_user_id("student-01"),
        "session_id": "session-01",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "env": "dev",
    }

    assert {event["event"] for event in api_events} >= {
        "request_received",
        "response_sent",
    }
    for event in api_events:
        for key, value in expected_context.items():
            assert event[key] == value


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
