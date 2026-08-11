# Báo cáo Day 13 — Observability cho hệ thống AI

> **Trạng thái:** Source/config/report đã được hoàn thiện. Các mục đánh dấu `CHƯA THU THẬP RUNTIME` bắt buộc phải lấy từ lần chạy thật của nhóm trước khi nộp cuối cùng. Không điền giả trace ID, screenshot, log hoặc commit SHA.

## 1. Thông tin nhóm

- **Tên nhóm:** B6-2
- **Repository:** https://github.com/thanhAI408/K4-DAY13-2A202601030
- **Cohort:** K4
- **Challenge:** `day13-k4-observability-v1`
- **Commit SHA cuối:** `CHƯA THU THẬP RUNTIME`

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

| Hạng mục | Mục tiêu | Kết quả |
|---|---:|---|
| `validate_logs.py` | ≥ 80/100 | `CHƯA THU THẬP RUNTIME` |
| Langfuse traces | ≥ 10 | `CHƯA THU THẬP RUNTIME` |
| PII leak | 0 | `CHƯA THU THẬP RUNTIME` |
| Dashboard validator | 6/6 panel | `CHƯA THU THẬP RUNTIME` |
| Public tests | PASS | `CHƯA THU THẬP RUNTIME` |

Evidence tương ứng được lưu trong `submission/evidence/` theo `submission/evidence/INDEX.md`.

## 3. Logging, correlation ID và PII

### 3.1 Structured JSON logging

Hệ thống dùng `structlog` và ghi log JSONL vào `data/logs.jsonl`. Các event API chính gồm `request_received`, `response_sent`, `request_failed` và log retrieval phục vụ điều tra incident.

Metadata quan trọng của request gồm:

- `correlation_id`
- `user_id_hash`
- `session_id`
- `feature`
- `model`
- `env`
- `latency_ms`
- `tokens_in`, `tokens_out`
- `cost_usd`
- `quality_score`

### 3.2 Correlation ID

Middleware xóa context cũ trước mỗi request, nhận `x-request-id` nếu hợp lệ hoặc sinh ID dạng `req-<8-hex>`, bind vào context logging và trả lại trên response header. Nhờ đó các event của cùng request có thể được nối lại bằng cùng một correlation ID.

- **Evidence:** `submission/evidence/07-log-correlation.json`
- **Correlation ID thật:** `CHƯA THU THẬP RUNTIME`

### 3.3 PII redaction

PII được scrub trước khi JSON được render và persist. Các loại được xử lý gồm:

- email;
- số điện thoại Việt Nam;
- CCCD 12 số;
- số thẻ thử nghiệm.

User ID không ghi nguyên văn mà được hash trước khi đưa vào metadata.

- **Evidence:** `submission/evidence/08-pii-redaction.json`
- **PII leak còn lại:** `CHƯA THU THẬP RUNTIME`

## 4. Tracing và prompt versioning

### 4.1 Trace

Langfuse dùng để ghi trace/generation và metadata cho mỗi request. Agent có các bước quan trọng để drill-down như retrieval và LLM call, giúp chuyển từ triệu chứng metric sang vị trí gây chậm cụ thể.

- **Trace list:** `submission/evidence/03-traces-list.png`
- **Trace waterfall:** `submission/evidence/04-trace-waterfall.png`
- **Trace ID minh họa:** `CHƯA THU THẬP RUNTIME`

### 4.2 Prompt versioning

- **Prompt name:** `day13-chat`
- **V1:** baseline; labels ban đầu `baseline`, `production`
- **V2:** candidate; label `candidate`
- **Mục tiêu:** chứng minh trace liên kết đúng `prompt_name`, `prompt_label`, `prompt_version`, sau đó đổi `production` sang V2 và rollback về V1.

Nếu Langfuse không khả dụng, hệ thống dùng local fallback và ghi `prompt_source=local` hoặc `local-fallback`, không giả vờ đã lấy managed prompt.

- **V1/V2 evidence:** `submission/evidence/05-prompt-versions.png`
- **Rollback evidence:** `submission/evidence/06-prompt-rollback.png`
- **Trace ID V1:** `CHƯA THU THẬP RUNTIME`
- **Trace ID V2:** `CHƯA THU THẬP RUNTIME`

## 5. Dashboard, SLO, alert và runbook

### 5.1 Dashboard contract

Nguồn chuẩn: `data/logs.jsonl`. Dashboard có 6 nhóm bắt buộc:

1. **Latency:** P50/P95/P99, đơn vị ms.
2. **Traffic:** request count / requests per minute.
3. **Errors:** error rate + breakdown theo `error_type`.
4. **Cost:** tổng cost theo thời gian và toàn cửa sổ.
5. **Tokens:** tổng input/output tokens.
6. **Quality:** average quality proxy.

- **Time range mặc định:** 60 phút.
- **Refresh:** 30 giây nếu công cụ hỗ trợ.
- **Validator:** `python scripts/validate_dashboard.py`.
- **Kết quả validator:** `CHƯA THU THẬP RUNTIME`.
- **Dashboard evidence:** `submission/evidence/10-dashboard.png`.

### 5.2 SLO

SLO/threshold thống nhất giữa dashboard, `config/slo.yaml`, alert rules và runbook:

- Latency P95 ≤ 3000 ms.
- Error rate ≤ 2%.
- Cost budget ≤ 2.5 USD.
- Quality average ≥ 0.75.

### 5.3 Alert

Ba alert chính:

- `high_latency_p95` — warning khi P95 vượt ngưỡng đủ lâu.
- `elevated_error_rate` — critical khi error rate vượt SLO.
- `cost_budget_exceeded` — warning khi cost vượt budget.

Mỗi alert có severity, condition/duration, owner và runbook trong `docs/alerts.md`.

## 6. Điều tra challenge chính thức K4

- **Challenge ID:** `day13-k4-observability-v1`
- **Incident:** `rag_slow`
- **Affected feature:** `monitoring`
- **Latency threshold của challenge:** 2000 ms

### 6.1 Triệu chứng

Khi challenge chạy, kỳ vọng tail latency tăng rõ rệt và vượt threshold chính thức. Metric phải được dùng để xác định request/khung thời gian bất thường trước khi drill-down trace.

- **Baseline metric:** `CHƯA THU THẬP RUNTIME`
- **Challenge metric:** `CHƯA THU THẬP RUNTIME`
- **Evidence:** `submission/evidence/11-challenge-metrics.png`

### 6.2 Trace và log chứng minh root cause

Root cause chỉ được kết luận sau khi trace và log thật cùng khớp. Với scenario chính thức `rag_slow`, bước retrieval bị thêm độ trễ; trace phải cho thấy span retrieval bất thường và log cùng correlation ID phải chứng minh thời gian của retrieval tăng.

- **Trace ID:** `CHƯA THU THẬP RUNTIME`
- **Correlation ID:** `CHƯA THU THẬP RUNTIME`
- **Trace evidence:** `submission/evidence/12-challenge-trace.png`
- **Log evidence:** `submission/evidence/13-challenge-log.json`

### 6.3 Root cause

**Root cause dự kiến theo scenario đã release:** retrieval/RAG dependency chậm, làm tăng end-to-end latency của request monitoring. Kết luận cuối cùng phải được xác nhận lại bằng trace ID và log line thật ở lần chạy challenge.

### 6.4 Fix action

- Tắt incident sau khi thu evidence.
- Đặt timeout cho retrieval.
- Có fallback/graceful degradation khi vector store chậm.
- Cache retrieval phù hợp.
- Tối ưu query/vector store khi xác định bottleneck thật.

### 6.5 Preventive measures

- Alert P95 dựa trên triệu chứng người dùng.
- Theo dõi latency riêng của retrieval span/dependency.
- Theo dõi timeout/error theo dependency.
- Dùng correlation ID để nối metric → trace → log trong runbook.
- Load test trước release để phát hiện tail latency regression.

## 7. Đóng góp cá nhân

> Commit/PR phải là link thật trên GitHub; không tự tạo link giả.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Văn Thành — 2A202601030 | Correlation ID, request metadata, structured logging, integration API | `CHƯA CÓ COMMIT/PR THẬT` | Contextvars, correlation ID, structured JSON log và evidence chain |
| Nguyễn Hoàng Hải — 2A202601426 | Langfuse tracing, prompt V1/V2, labels, rollback | `CHƯA CÓ COMMIT/PR THẬT` | Trace/span, prompt versioning và rollback an toàn |
| Nguyễn Duy Khánh — 2A202601530 | Dashboard 6 panel, SLO, alert rules, runbook | `CHƯA CÓ COMMIT/PR THẬT` | P50/P95/P99, SLO, alert theo triệu chứng và runbook |
| Ngô Xuân Ninh — 2A202601068 | Challenge investigation, evidence chain, report/demo | `CHƯA CÓ COMMIT/PR THẬT` | Metrics → Traces → Logs → Root cause → Fix → Prevention |
| Nguyễn Chiến Thắng — 2A202601734 | PII redaction, tests, validator, pre-submit hygiene | `CHƯA CÓ COMMIT/PR THẬT` | PII scrubbing trước persist, validation và secret hygiene |

## 8. Checklist trước khi nộp cuối

- [ ] `python -m pytest -q` PASS.
- [ ] `python scripts/validate_logs.py` ≥ 80/100.
- [ ] `python scripts/validate_dashboard.py` = 6/6 panel.
- [ ] Langfuse có ≥ 10 traces.
- [ ] Có trace waterfall.
- [ ] Có V1/V2 + label switch/rollback evidence.
- [ ] Correlation ID và PII redaction evidence hợp lệ.
- [ ] Dashboard đủ 6 nhóm và thấy threshold/SLO.
- [ ] Challenge có metric + trace ID + log/correlation ID thật.
- [ ] Thay toàn bộ `CHƯA THU THẬP RUNTIME` bằng kết quả thật.
- [ ] Thay toàn bộ `CHƯA CÓ COMMIT/PR THẬT` bằng link thật nếu rubric yêu cầu từng thành viên.
- [ ] `.env` và secret không bị Git track.
- [ ] `config/challenge.json` không bị sửa.
