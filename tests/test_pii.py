from app.logging_config import scrub_event
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


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD 012345678901 issued in 2021")
    assert "012345678901" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    for card in ("1234567812345678", "1234 5678 1234 5678", "1234-5678-1234-5678"):
        out = scrub_text(f"Card: {card}")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_passport() -> None:
    out = scrub_text("Passport B1234567 expires soon")
    assert "B1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_vietnamese_address() -> None:
    out = scrub_text("Giao tới số nhà 12, đường Lê Lợi")
    assert "số nhà" not in out
    assert "REDACTED_ADDRESS_VN" in out


def test_scrub_event_redacts_every_string_field() -> None:
    event = {
        "event": "email me at leak@example.com",
        "session_id": "call 0901234567",
        "payload": {"detail": "card 1234 5678 1234 5678", "count": 3},
    }
    out = scrub_event(None, "info", event)

    # Both top-level string fields and one level of nested dict are scrubbed.
    assert "leak@example.com" not in out["event"]
    assert "0901234567" not in out["session_id"]
    assert "1234 5678 1234 5678" not in out["payload"]["detail"]
    # Non-string values are passed through untouched.
    assert out["payload"]["count"] == 3
