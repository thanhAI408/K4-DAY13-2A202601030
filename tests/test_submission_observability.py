from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def test_chat_has_correlation_metadata_and_redacts_pii(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "req-1234abcd"},
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "monitoring",
                "message": "My email is student@vinuni.edu.vn and phone 090 123 4567. Explain logs.",
            },
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-1234abcd"
    assert response.json()["correlation_id"] == "req-1234abcd"

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_records = [record for record in records if record.get("service") == "api"]
    assert api_records
    assert all(record["correlation_id"] == "req-1234abcd" for record in api_records)
    assert all(record.get("user_id_hash") for record in api_records)
    assert all(record.get("session_id") == "session-01" for record in api_records)
    assert all(record.get("feature") == "monitoring" for record in api_records)
    assert all(record.get("model") for record in api_records)
    assert all(record.get("env") for record in api_records)

    raw = log_path.read_text(encoding="utf-8")
    assert "student@vinuni.edu.vn" not in raw
    assert "090 123 4567" not in raw
    assert "REDACTED_EMAIL" in raw
    assert "REDACTED_PHONE_VN" in raw


def test_invalid_incoming_request_id_is_replaced(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "not-valid"},
            json={
                "user_id": "u01",
                "session_id": "s01",
                "feature": "monitoring",
                "message": "Explain observability",
            },
        )

    request_id = response.headers["x-request-id"]
    assert request_id.startswith("req-")
    assert len(request_id) == 12
    assert request_id != "not-valid"
