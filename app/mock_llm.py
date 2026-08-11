from __future__ import annotations

import time
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "fake-observability-llm-v1") -> None:
        self.model = model

    def _answer_from_prompt(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "refunds are available within 7 days" in lowered:
            return "Refunds are available within 7 days and require proof of purchase."
        if "pii and sensitive data" in lowered or "do not expose pii" in lowered:
            return (
                "PII and other sensitive data must not appear raw in application logs. "
                "Redact email, phone, identity and payment data before persisting the log."
            )
        if "alerts should be symptom-based" in lowered:
            return (
                "A useful alert is tied to an SLO and a user-visible symptom. "
                "It should define a threshold, duration, severity, owner and runbook."
            )
        if "metrics detect incidents" in lowered or "tail latency" in lowered:
            return (
                "Metrics show that an incident exists, for example a P95/P99 latency increase. "
                "Traces localize the slow or failed span, and logs with the same correlation ID "
                "provide detailed evidence that explains the root cause."
            )
        return (
            "Use metrics to detect the symptom, traces to localize the abnormal step, "
            "and correlated logs to confirm the root cause before deciding a fix."
        )

    def generate(self, prompt: str) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        answer = self._answer_from_prompt(prompt)

        if STATE["cost_spike"]:
            detail = (
                " Additional detail: compare traffic with input/output token totals, inspect prompt version, "
                "and cap response length when cost rises without a matching traffic increase."
            )
            answer += detail * 6

        output_tokens = max(20, len(answer) // 4)
        return FakeResponse(
            text=answer,
            usage=FakeUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            model=self.model,
        )
