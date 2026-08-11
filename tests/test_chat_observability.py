from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from app.pii import hash_user_id


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    monkeypatch.setenv("APP_ENV", "test")

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]
    assert response_event["correlation_id"] == response.json()["correlation_id"]
    assert response_event["user_id_hash"] == hash_user_id("student-01")
    assert response_event["session_id"] == "session-01"
    assert response_event["feature"] == "qa"
    assert response_event["model"] == "claude-sonnet-4-5"
    assert response_event["env"] == "test"
    assert "student-01" not in json.dumps(response_event)


def test_middleware_generates_correlation_id_and_response_timing() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    correlation_id = response.headers["x-request-id"]
    assert response.status_code == 200
    assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
    assert response.headers["x-response-time-ms"].isdigit()


def test_middleware_preserves_valid_incoming_request_id() -> None:
    incoming_id = "req-deadbeef"

    with TestClient(app) as client:
        response = client.get("/health", headers={"x-request-id": incoming_id})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == incoming_id


def test_middleware_replaces_malformed_incoming_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"x-request-id": "email@example.com"})

    assert response.status_code == 200
    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])
