# Official challenge: `day13-k4-observability-v1`

Incident: `rag_slow` · affected feature: `monitoring` · threshold: 2000 ms.

## 1. Symptom from metrics/log aggregates

The official run produced five monitoring responses above 3000 ms:

| Correlation ID | Latency |
|---|---:|
| `req-e07061ff` | 3573 ms |
| `req-ab2deb95` | 3584 ms |
| `req-78853200` | 3607 ms |
| `req-ade71be9` | 3712 ms |
| `req-f3aa1422` | 3599 ms |

Across the current JSONL artifact there are 100 records, 33 API requests, 33
responses, and the five official slow responses. The overall response latency
range is 1009–3712 ms with an average of 1507.91 ms.

## 2. Trace localization

Trace `bf1efca04158b1963ed2a9048a5b16db` has the same correlation ID as the
first slow response and shows a 3.573-second `run` generation observation.
See [`trace-waterfall.md`](trace-waterfall.md).

## 3. Log proof of root cause

- `incident_enabled` for `rag_slow`: correlation ID `req-e486e6a2`,
  `2026-08-11T10:07:07.578195Z`.
- Five slow `response_sent` records share `feature=monitoring` and their
  correlation IDs with the trace/request pairs above.
- `incident_disabled` for `rag_slow`: correlation ID `req-0cbbb951`,
  `2026-08-11T10:08:18.003537Z`.
- [`app/mock_rag.py`](../../app/mock_rag.py) contains the incident behavior:
  `if STATE["rag_slow"]: time.sleep(2.5)`.
- [`app/mock_llm.py`](../../app/mock_llm.py) sleeps only 0.15 seconds, so the
  added tail latency is attributable to the RAG branch rather than generation.

## 4. Fix and prevention

- Immediate mitigation: disable `rag_slow` and verify P95 returns below the
  3000-ms SLO line.
- Code-level fix: remove the blocking failure injection in production, add a
  bounded RAG timeout/fallback, and instrument RAG and LLM as child spans.
- Prevention: keep the latency/error alerts enabled, retain correlation IDs
  through middleware, and run the official challenge/load test in CI before
  release.
