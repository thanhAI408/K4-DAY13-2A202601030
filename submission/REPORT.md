# Báo cáo Day 13 — Observability cho hệ thống AI

> **Trạng thái:** Đã hoàn thiện code và config. Evidence runtime cần thu thập sau khi chạy thật API với Langfuse.

## 1. Thông tin nhóm

- **Tên nhóm:** B6-2
- **Repository:** https://github.com/thanhAI408/K4-DAY13-2A202601030
- **Cohort:** K4
- **Challenge:** `day13-k4-observability-v1`
- **Commit SHA cuối:** `cf5f8ef8d9b640da8abc3cab6b9158ac60cd1944`

### Thành viên và vai trò

| Thành viên | MSSV | Vai trò chính |
|---|---|---|
| Nguyễn Văn Thành | 2A202601030 | Logging & PII / Integration |
| Nguyễn Hoàng Hải | 2A202601426 | Tracing & Prompt Versioning |
| Nguyễn Duy Khánh | 2A202601530 | Dashboard, SLO & Alert |
| Ngô Xuân Ninh | 2A202601068 | Incident, Report & Demo |
| Nguyễn Chiến Thắng | 2A202601734 | PII, Tests & Validation |

Nhóm có 5 thành viên nhưng vẫn bám theo 4 nhóm vai trò chính của lab; hai thành viên cùng chia phần Logging & PII / validation.

## 2. Kết quả kỹ thuật

| Hạng mục | Mục tiêu | Kết quả | Evidence |
|---|---:|---|---|---|
| `validate_logs.py` | ≥ 80/100 | Cần chạy runtime | `submission/evidence/02-validate-logs.txt` |
| Langfuse traces | ≥ 10 | Cần chạy runtime | `submission/evidence/03-traces-list.png` |
| PII leak | 0 | Code đã impl, cần test | `submission/evidence/08-pii-redaction.json` |
| Dashboard validator | 6/6 panel | **ĐÃ VALIDATE** | `submission/evidence/09-validate-dashboard.txt` |
| Public tests | PASS | Cần chạy runtime | `python -m pytest -q` |

## 3. Triển khai kỹ thuật đã hoàn thành

### 3.1 Structured JSON Logging (`app/logging_config.py`)

Dùng `structlog` với các processors:
- `merge_contextvars` - merge correlation ID từ context
- `add_log_level` - thêm level
- `TimeStamper` - timestamp ISO UTC
- `scrub_event` - PII redaction trước khi persist
- `JsonlFileProcessor` - ghi JSONL vào `data/logs.jsonl`

### 3.2 Correlation ID (`app/middleware.py`)

Middleware `CorrelationIdMiddleware`:
- Clear contextvars trước mỗi request
- Accept `x-request-id` header nếu hợp lệ (`req-<8-hex>`)
- Sinh `req-<8-hex>` nếu không có header
- Bind `correlation_id` vào context
- Trả lại `x-request-id` và `x-response-time-ms` headers

### 3.3 PII Redaction (`app/pii.py`)

Hỗ trợ các pattern:
- Email: `\w+@[\w.-]+\.\w+`
- Phone VN: `(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)`
- CCCD 12 số: `\b\d{12}\b`
- Credit Card: `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b`

Replace bằng `[REDACTED_<TYPE>]`

### 3.4 Tracing (`app/tracing.py`, `app/agent.py`)

- Dùng Langfuse SDK với `@observe` decorator
- Span `retrieval` và `llm_call` cho drill-down
- Metadata: `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`
- Fallback local khi Langfuse không khả dụng

### 3.5 Prompt Versioning (`app/prompt_management.py`)

- Prompt name: `day13-chat`
- V1: labels `baseline`, `production`
- V2: label `candidate`
- Hỗ trợ switch label và rollback

### 3.6 Dashboard (`config/dashboard.yaml`)

6 panels đã validate:
1. **Latency** - P50/P95/P99, threshold P95 ≤ 3000ms
2. **Traffic** - count/rate, threshold rate ≥ 1
3. **Errors** - error rate %, threshold ≤ 2%
4. **Cost** - sum USD, threshold ≤ $2.5
5. **Tokens** - sum tokens, threshold ≤ 50000
6. **Quality** - mean score, threshold ≥ 0.75

Validator: `HỢP LỆ: 6/6 panel`

### 3.7 SLO (`config/slo.yaml`)

| SLI | Objective | Target |
|---|---|---|
| latency_p95_ms | 3000ms | 99.5% |
| error_rate_pct | 2% | 99.0% |
| daily_cost_usd | $2.5 | 100% |
| quality_score_avg | 0.75 | 95% |

### 3.8 Alerts (`config/alert_rules.yaml`)

3 alerts symptom-based:
1. `high_latency_p95` - warning, P95 > 3000ms for 5m
2. `elevated_error_rate` - critical, error > 2% for 3m
3. `cost_budget_exceeded` - warning, daily > $2.5

## 4. Challenge Investigation

- **Challenge ID:** `day13-k4-observability-v1`
- **Scenario:** `rag_slow`
- **Latency threshold:** 2000ms

### Root Cause dự kiến

Retrieval span chậm bất thường (> 2000ms) làm tăng end-to-end latency.

### Fix Actions
- Disable incident sau khi thu evidence
- Đặt timeout cho retrieval
- Implement fallback/graceful degradation
- Cache retrieval results

### Preventive Measures
- Alert P95 dựa trên triệu chứng
- Monitor retrieval span latency riêng
- Load test trước release

## 5. Evidence Files

| # | File | Status |
|---:|---|---|
| 1 | `01-health.png` | Cần chạy API |
| 2 | `02-validate-logs.txt` | Cần chạy load_test |
| 3 | `03-traces-list.png` | Cần Langfuse |
| 4 | `04-trace-waterfall.png` | Cần Langfuse |
| 5 | `05-prompt-versions.png` | Cần Langfuse |
| 6 | `06-prompt-rollback.png` | Cần Langfuse |
| 7 | `07-log-correlation.json` | Đã có mẫu |
| 8 | `08-pii-redaction.json` | Đã có mẫu |
| 9 | `09-validate-dashboard.txt` | **ĐÃ VALIDATE** |
| 10 | `10-dashboard.png` | Cần chạy build_dashboard |
| 11 | `11-challenge-metrics.png` | Cần chạy challenge |
| 12 | `12-challenge-trace.png` | Cần chạy challenge |
| 13 | `13-challenge-log.json` | Đã có mẫu |

## 6. Đóng góp cá nhân

| Thành viên | Phần việc | Commit |
|---|---|---|
| Nguyễn Văn Thành | Correlation ID, middleware, logging | cf5f8ef |
| Nguyễn Hoàng Hải | Langfuse tracing, prompt versioning | cf5f8ef |
| Nguyễn Duy Khánh | Dashboard, SLO, alerts | cf5f8ef |
| Ngô Xuân Ninh | Challenge investigation | cf5f8ef |
| Nguyễn Chiến Thắng | PII redaction, validation | cf5f8ef |

## 7. Hướng dẫn thu thập Evidence Runtime

```bash
# 1. Setup môi trường
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Điền LANGFUSE_* keys

# 2. Chạy API
uvicorn app.main:app --reload --env-file .env

# 3. Chạy load test (terminal khác)
python scripts/load_test.py --concurrency 5

# 4. Validate logs
python scripts/validate_logs.py

# 5. Build dashboard
python scripts/build_dashboard.py

# 6. Challenge (sau khi release)
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5

# 7. Thu evidence
python scripts/collect_evidence.py

# 8. Tests
python -m pytest -q
```

## 8. Checklist trước khi nộp

- [ ] API chạy và `/health` trả `ok: true`
- [ ] `python scripts/validate_logs.py` ≥ 80/100
- [ ] `python scripts/validate_dashboard.py` = 6/6 panel
- [ ] Langfuse có ≥ 10 traces
- [ ] Có trace waterfall (retrieval + llm_call spans)
- [ ] Có V1/V2 prompt versions + label switch/rollback evidence
- [ ] PII redaction verified (no leaks)
- [ ] Dashboard 6 panels với threshold visible
- [ ] Challenge có metric + trace + log evidence
- [ ] `python -m pytest -q` PASS
- [ ] Không có `.env` hoặc secrets trong git
