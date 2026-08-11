import json

from app import logging_config
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_identity_and_card_numbers() -> None:
    out = scrub_text("CCCD 012345678901, passport B12345678, card 4111 1111 1111 1111")

    assert "012345678901" not in out
    assert "B12345678" not in out
    assert "4111 1111 1111 1111" not in out
    assert "REDACTED_CCCD" in out
    assert "REDACTED_PASSPORT" in out
    assert "REDACTED_CREDIT_CARD" in out


def test_jsonl_logging_scrubs_nested_payload(
    monkeypatch, tmp_path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    logging_config.get_logger().info(
        "pii_test",
        service="api",
        payload={
            "nested": {"email": "student@vinuni.edu.vn"},
            "items": ["090 123 4567", "4111 1111 1111 1111"],
        },
    )

    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    raw = json.dumps(record, ensure_ascii=False)

    assert "student@vinuni.edu.vn" not in raw
    assert "090 123 4567" not in raw
    assert "4111 1111 1111 1111" not in raw
    assert "REDACTED_EMAIL" in raw
    assert "REDACTED_PHONE_VN" in raw
    assert "REDACTED_CREDIT_CARD" in raw
