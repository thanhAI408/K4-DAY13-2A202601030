from collections import Counter

from app import metrics
from app.metrics import calculate_error_rate_pct, percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_returns_zero_without_requests() -> None:
    assert calculate_error_rate_pct(0, 1) == 0.0


def test_error_rate_is_failed_requests_over_total_requests() -> None:
    assert calculate_error_rate_pct(20, 3) == 15.0


def test_snapshot_tracks_failed_requests_in_error_rate(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 10)
    monkeypatch.setattr(metrics, "FAILED_REQUESTS", 2)
    monkeypatch.setattr(metrics, "REQUEST_LATENCIES", [])
    monkeypatch.setattr(metrics, "REQUEST_COSTS", [])
    monkeypatch.setattr(metrics, "REQUEST_TOKENS_IN", [])
    monkeypatch.setattr(metrics, "REQUEST_TOKENS_OUT", [])
    monkeypatch.setattr(metrics, "QUALITY_SCORES", [])
    monkeypatch.setattr(metrics, "ERRORS", Counter({"RuntimeError": 2}))

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 10
    assert snapshot["requests_failed"] == 2
    assert snapshot["error_rate_pct"] == 20.0
    assert snapshot["error_breakdown"] == {"RuntimeError": 2}
