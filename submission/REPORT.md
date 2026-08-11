# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Cohort/challenge: `K4` / `day13-k4-observability-v1`
- Branch nộp bài: `2A202601530`
- Repository: <https://github.com/thanhAI408/K4-DAY13-2A202601030>
- Commit SHA cuối: lấy bằng `git rev-parse HEAD` trên branch nộp bài.
- `.env`, API key, `.venv` và log runtime không được commit.

## 2. Kết quả kỹ thuật

- `scripts/validate_logs.py`: **100/100**; 0 missing required fields, 0
  missing enrichment, 0 potential PII leaks.
- `scripts/validate_dashboard.py`: **6/6 panel hợp lệ**.
- Langfuse: **79 traces** sau khi flush graceful; danh sách representative nằm
  trong [`trace-list.md`](evidence/trace-list.md).
- PII leak còn lại trong JSONL: **0**.
- Dashboard runtime: [`dashboard/streamlit_app.py`](../dashboard/streamlit_app.py),
  chạy bằng `streamlit run dashboard/streamlit_app.py`.

Evidence validator: [`validate_logs.txt`](evidence/validate_logs.txt),
[`validate_dashboard.txt`](evidence/validate_dashboard.txt).

## 3. Logging, metrics và tracing

- Middleware tạo/reuse correlation ID dạng `req-<8 hex>`, bind contextvars
  trước `request_received` và xóa context ở cuối request.
- API logs có `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- PII được scrub đệ quy trước khi ghi JSONL; raw user ID không xuất hiện.
- Metrics có request counter, failed counter và `error_rate_pct`; dashboard
  có sáu nhóm latency, traffic, errors, cost, tokens và quality.
- Trace metadata liên kết `correlation_id`, `env`, prompt name/label/version và
  generation usage/cost.
- Trace waterfall challenge: [`trace-waterfall.md`](evidence/trace-waterfall.md).
- PII evidence: [`pii-redaction.md`](evidence/pii-redaction.md).

## 4. Prompt versioning

- Prompt: `day13-chat`, type `text`.
- Version 1: template baseline, labels `baseline` và `production`.
- Version 2: thêm format hướng dẫn trả lời ngắn gọn, label `candidate`.
- Đã chạy cùng một input qua baseline/candidate, promote production sang v2,
  rồi rollback production về v1.
- Trace IDs và trạng thái label cuối: [`traces-prompt-versioning.md`](evidence/traces-prompt-versioning.md).

## 5. Dashboard, SLO và alerts

- Dashboard contract: đúng sáu panel, time range 60 phút, refresh 30 giây,
  đơn vị và threshold được kiểm tra tự động.
- SLO: P95 latency ≤ 3000 ms trong 99.5% cửa sổ 5 phút; error rate ≤ 2%;
  daily cost ≤ 2.5 USD; average quality ≥ 0.75.
- Alert rules: latency SLO breach, error-rate SLO breach và daily-cost budget
  breach; mỗi alert có severity, owner, condition và runbook.
- Runbook: [`docs/alerts.md`](../docs/alerts.md).
- Dashboard evidence: [`dashboard-panels.md`](evidence/dashboard-panels.md),
  [`dashboard-runtime.txt`](evidence/dashboard-runtime.txt).

## 6. Điều tra challenge

- Challenge: `day13-k4-observability-v1`, incident `rag_slow`.
- Metrics/log symptom: 5 official monitoring responses từ 3573 đến 3712 ms,
  đều vượt threshold 2000 ms và latency SLO 3000 ms.
- Trace: `bf1efca04158b1963ed2a9048a5b16db`, correlation ID `req-e07061ff`,
  generation span 3.573 s.
- Root cause: `app/mock_rag.py` injects `time.sleep(2.5)` khi `STATE["rag_slow"]`
  bật; fake LLM chỉ thêm 0.15 s.
- Fix action: disable incident; production fix là loại bỏ blocking delay, thêm
  timeout/fallback cho RAG và child spans.
- Preventive measure: SLO alerts, correlation-linked trace/log investigation,
  CI challenge/load test và PII-safe structured logging.
- Full evidence: [`challenge-rag-slow.md`](evidence/challenge-rag-slow.md).

## 7. Đóng góp cá nhân/nhóm

| Thành viên | Phần việc | Commit/evidence |
|---|---|---|
| A | Middleware, correlation ID, exception/request context | `bb84f9d` |
| B | PII patterns, scrubber và log validation tests | `bb84f9d` |
| C | Metrics `error_rate_pct`, dashboard contract/runtime và validator | `9f08b7c`, `dashboard/streamlit_app.py` |
| D | SLO, alert rules và incident runbook | commit hiện tại, `config/alert_rules.yaml`, `docs/alerts.md` |
| E | Trace context, prompt linkage và challenge investigation | `79c3646`, `submission/evidence/` |

Các commit CP1/CP2 trước đó đã được push lên branch `2A202601530`; commit mới
chứa alert/runbook, dashboard runtime và evidence/report sẽ được push cùng branch.
