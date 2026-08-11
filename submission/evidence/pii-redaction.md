# PII redaction evidence

- The final log validator detected `0` potential PII leaks.
- Request context contains `user_id_hash`; raw `user_id` is not logged.
- The scrubber covers email, Vietnamese phone numbers, CCCD and credit-card
  patterns before the JSONL processor writes a record.
- Observed sanitized preview: `What is your refund policy? My email is [REDACTED_EMAIL]`.
- Observed sanitized preview: `What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?`.
- Automated tests cover both direct detector cases and nested structured-log
  payloads (`tests/test_pii.py`, `tests/test_chat_observability.py`).
