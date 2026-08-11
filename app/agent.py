from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from . import metrics
from .logging_config import get_logger
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, tracing_enabled

T = TypeVar("T")
log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    retrieval_latency_ms: int
    llm_latency_ms: int
    prompt_name: str
    prompt_label: str
    prompt_version: str
    prompt_source: str


class LabAgent:
    def __init__(self, model: str = "fake-observability-llm-v1") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    def _observed_step(self, name: str, callback: Callable[[], T]) -> tuple[T, int]:
        started = time.perf_counter()
        client = get_langfuse_client()
        if tracing_enabled() and hasattr(client, "start_as_current_observation"):
            with client.start_as_current_observation(as_type="span", name=name) as span:
                result = callback()
                latency_ms = int((time.perf_counter() - started) * 1000)
                update = getattr(span, "update", None)
                if callable(update):
                    update(metadata={"latency_ms": latency_ms})
                return result, latency_ms
        result = callback()
        return result, int((time.perf_counter() - started) * 1000)

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()

        retrieval_started = time.perf_counter()
        try:
            docs, retrieval_latency_ms = self._observed_step("retrieval", lambda: retrieve(message))
            log.info(
                "retrieval_completed",
                service="retrieval",
                tool_name="mock_vector_store",
                latency_ms=retrieval_latency_ms,
                payload={"doc_count": len(docs)},
            )
        except Exception as exc:
            retrieval_latency_ms = int((time.perf_counter() - retrieval_started) * 1000)
            log.error(
                "retrieval_failed",
                service="retrieval",
                tool_name="mock_vector_store",
                latency_ms=retrieval_latency_ms,
                error_type=type(exc).__name__,
                payload={"detail": str(exc)},
            )
            raise

        langfuse_client = get_langfuse_client()
        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )

        response, llm_latency_ms = self._observed_step(
            "llm_call", lambda: self.llm.generate(prompt.text)
        )
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        log.info(
            "llm_completed",
            service="llm",
            latency_ms=llm_latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            payload={"prompt_version": prompt.version, "prompt_label": prompt.label},
        )

        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
            metadata={
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
            },
        )
        langfuse_client.update_current_generation(
            model=self.model,
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "retrieval_latency_ms": retrieval_latency_ms,
                "llm_latency_ms": llm_latency_ms,
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
            },
            usage_details={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            cost_details={"total": cost_usd},
            prompt=prompt.managed_prompt,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            prompt_name=prompt.name,
            prompt_label=prompt.label,
            prompt_version=prompt.version,
            prompt_source=prompt.source,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        question_tokens = [token.strip("?,.!:") for token in question.lower().split()[:6]]
        if any(token and token in answer.lower() for token in question_tokens):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
