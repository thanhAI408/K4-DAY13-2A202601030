from __future__ import annotations

import hashlib
import re

# Order matters: re.sub is applied sequentially, so longer / more specific
# patterns run first to avoid a general pattern redacting part of a value and
# breaking a later match (e.g. a 16-digit card being clipped by the phone rule).
PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    # 16-digit card (grouped or not) — must precede phone/cccd numeric rules.
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # CCCD/CMND: 12 digits (new) — before phone so it is not partially eaten.
    "cccd": r"\b\d{12}\b",
    # Counts 9 digits after the +84/0 prefix so spaced/dotted/dashed formats
    # (090 123 4567, +84 90 123 4567) are also caught — do NOT weaken this.
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    # VN passport: 1 letter + 7 digits (e.g. B1234567), e-passport 1 letter + 8.
    "passport": r"\b[A-Z]\d{7,8}\b",
    # Vietnamese address marker keywords.
    "address_vn": r"\b(?:số nhà|đường|phường|quận|huyện|tỉnh|thành phố)\b",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
