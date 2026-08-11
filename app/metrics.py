from __future__ import annotations

from collections import Counter
from statistics import mean
from threading import Lock

_METRICS_LOCK = Lock()
REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
FAILED_REQUESTS: int = 0
QUALITY_SCORES: list[float] = []


def record_request_started() -> None:
    """Count a request when the chat endpoint accepts it.

    This counter is intentionally updated before agent execution so failed
    requests remain part of the error-rate denominator.
    """
    global TRAFFIC
    with _METRICS_LOCK:
        TRAFFIC += 1


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    with _METRICS_LOCK:
        REQUEST_LATENCIES.append(latency_ms)
        REQUEST_COSTS.append(cost_usd)
        REQUEST_TOKENS_IN.append(tokens_in)
        REQUEST_TOKENS_OUT.append(tokens_out)
        QUALITY_SCORES.append(quality_score)



def record_error(error_type: str) -> None:
    """Record one failed request and its error category."""
    global FAILED_REQUESTS
    with _METRICS_LOCK:
        FAILED_REQUESTS += 1
        ERRORS[error_type] += 1


def calculate_error_rate_pct(total_requests: int, failed_requests: int) -> float:
    if total_requests <= 0:
        return 0.0
    return round((failed_requests / total_requests) * 100, 4)



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    with _METRICS_LOCK:
        traffic = TRAFFIC
        failed_requests = FAILED_REQUESTS
        latencies = list(REQUEST_LATENCIES)
        costs = list(REQUEST_COSTS)
        tokens_in = list(REQUEST_TOKENS_IN)
        tokens_out = list(REQUEST_TOKENS_OUT)
        quality_scores = list(QUALITY_SCORES)
        error_breakdown = dict(ERRORS)

    return {
        "traffic": traffic,
        "requests_failed": failed_requests,
        "error_rate_pct": calculate_error_rate_pct(traffic, failed_requests),
        "latency_p50": percentile(latencies, 50),
        "latency_p95": percentile(latencies, 95),
        "latency_p99": percentile(latencies, 99),
        "avg_cost_usd": round(mean(costs), 4) if costs else 0.0,
        "total_cost_usd": round(sum(costs), 4),
        "tokens_in_total": sum(tokens_in),
        "tokens_out_total": sum(tokens_out),
        "error_breakdown": error_breakdown,
        "quality_avg": round(mean(quality_scores), 4) if quality_scores else 0.0,
    }
