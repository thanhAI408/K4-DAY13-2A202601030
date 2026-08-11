# Dashboard evidence

The dashboard contract was validated with `scripts/validate_dashboard.py` and
contains exactly six panels:

| Panel | Source fields | Aggregation | Threshold |
|---|---|---|---|
| Latency | `response_sent.latency_ms` | P50/P95/P99 | P95 ≤ 3000 ms |
| Traffic | `request_received` | count/rate per minute | rate ≥ 1 request/min |
| Errors | `request_received`, `request_failed`, `error_type` | error rate/breakdown | error rate ≤ 2% |
| Cost | `response_sent.cost_usd` | sum by minute/total | total ≤ 2.5 USD |
| Tokens | `tokens_in`, `tokens_out` | sum by field | total ≤ 50000 |
| Quality | `response_sent.quality_score` | mean | mean ≥ 0.75 |

Runtime implementation: [`dashboard/streamlit_app.py`](../../dashboard/streamlit_app.py).
The runtime smoke check read 28 records in the latest 60-minute window and
computed P95 latency of 1500 ms. The validator output is recorded in
[`validate_dashboard.txt`](validate_dashboard.txt).
