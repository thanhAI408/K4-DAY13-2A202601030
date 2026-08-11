from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
WINDOW_MINUTES = 60


def load_records(path: Path = LOG_PATH) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            record["_ts"] = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        records.append(record)
    return records


def select_window(records: list[dict], minutes: int = WINDOW_MINUTES) -> list[dict]:
    if not records:
        return []
    end = max(record["_ts"] for record in records)
    start = end - timedelta(minutes=minutes)
    return [record for record in records if start <= record["_ts"] <= end]


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def threshold_status(value: float, threshold: float, *, lower_is_better: bool) -> str:
    passed = value <= threshold if lower_is_better else value >= threshold
    return "✅ within threshold" if passed else "⚠️ threshold breached"


def show_dashboard(records: list[dict]) -> None:
    st.set_page_config(page_title="Day 13 AI Observability", layout="wide")
    st.title("Day 13 AI Observability")
    st.caption(
        "Source: data/logs.jsonl · time range: 60 minutes · refresh contract: 30 seconds · "
        "aggregates only, no raw user message displayed"
    )
    if st.button("Refresh data"):
        st.rerun()

    window = select_window(records)
    responses = [record for record in window if record.get("event") == "response_sent"]
    requests = [record for record in window if record.get("event") == "request_received"]
    failures = [record for record in window if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in responses if record.get("latency_ms") is not None]
    costs = [float(record["cost_usd"]) for record in responses if record.get("cost_usd") is not None]
    tokens_in = [int(record["tokens_in"]) for record in responses if record.get("tokens_in") is not None]
    tokens_out = [int(record["tokens_out"]) for record in responses if record.get("tokens_out") is not None]
    qualities = [float(record["quality_score"]) for record in responses if record.get("quality_score") is not None]

    if not window:
        st.warning("No valid JSON records were found in the selected window.")
        return

    st.info(f"Showing {len(window)} records from the latest {WINDOW_MINUTES}-minute window.")

    st.subheader("Latency percentiles")
    p50 = percentile(latencies, 0.50)
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)
    latency_columns = st.columns(4)
    latency_columns[0].metric("P50", f"{p50:.0f} ms")
    latency_columns[1].metric("P95", f"{p95:.0f} ms")
    latency_columns[2].metric("P99", f"{p99:.0f} ms")
    latency_columns[3].write(threshold_status(p95, 3000, lower_is_better=True))
    if latencies:
        st.line_chart({"response latency (ms)": latencies}, height=180)

    st.subheader("Request traffic")
    traffic_columns = st.columns(3)
    traffic_columns[0].metric("Requests", len(requests))
    traffic_columns[1].metric("Responses", len(responses))
    traffic_columns[2].metric("Rate", f"{len(requests) / WINDOW_MINUTES:.2f} req/min")

    st.subheader("Error rate and breakdown")
    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    error_columns = st.columns(3)
    error_columns[0].metric("Error rate", f"{error_rate:.2f}%")
    error_columns[1].metric("Failed requests", len(failures))
    error_columns[2].write(threshold_status(error_rate, 2, lower_is_better=True))
    error_types: dict[str, int] = {}
    for record in failures:
        error_type = str(record.get("error_type") or "unknown")
        error_types[error_type] = error_types.get(error_type, 0) + 1
    st.json(error_types or {"none": 0})

    st.subheader("Cost over time")
    cost_columns = st.columns(3)
    total_cost = sum(costs)
    cost_columns[0].metric("Total cost", f"${total_cost:.4f}")
    cost_columns[1].metric("Average/request", f"${(total_cost / len(responses)) if responses else 0:.4f}")
    cost_columns[2].write(threshold_status(total_cost, 2.5, lower_is_better=True))

    st.subheader("Input and output tokens")
    token_columns = st.columns(3)
    token_columns[0].metric("Input", f"{sum(tokens_in):,}")
    token_columns[1].metric("Output", f"{sum(tokens_out):,}")
    token_columns[2].metric("Total", f"{sum(tokens_in) + sum(tokens_out):,}")

    st.subheader("Quality proxy")
    quality_columns = st.columns(2)
    average_quality = safe_mean(qualities)
    quality_columns[0].metric("Average quality", f"{average_quality:.2f}")
    quality_columns[1].write(threshold_status(average_quality, 0.75, lower_is_better=False))


if __name__ == "__main__":
    show_dashboard(load_records())
