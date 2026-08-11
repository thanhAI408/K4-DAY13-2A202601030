from __future__ import annotations

import time

from .incidents import STATE

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": [
        "Metrics detect incidents, traces localize slow or failed spans, and logs explain root cause using a shared correlation ID.",
        "Tail latency should be investigated with P95/P99, then a slow trace, then correlated logs.",
    ],
    "policy": ["PII and sensitive data must not appear raw in application logs. Use sanitized summaries only."],
    "alert": ["Alerts should be symptom-based, tied to an SLO, have a duration, severity, owner and runbook."],
}

KEYWORDS = {
    # Ưu tiên intent cụ thể trước từ khóa monitoring chung như "log".
    "refund": ("refund", "purchase"),
    "policy": (
        "policy",
        "pii",
        "sensitive",
        "credit card",
        "email",
        "phone",
        "should not appear",
        "not appear in app logs",
    ),
    "alert": ("alert", "slo", "threshold", "runbook"),
    "monitoring": (
        "monitoring",
        "observability",
        "metric",
        "trace",
        "log",
        "latency",
        "p95",
        "p99",
        "span",
        "root cause",
    ),
}


def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)

    lowered = message.lower()
    for topic, keywords in KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return CORPUS[topic]
    return ["No domain document matched. Use a concise general observability fallback answer."]
