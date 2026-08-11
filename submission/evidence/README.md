# Evidence checklist — Day 13 K4

Không làm giả evidence. Tất cả file dưới đây phải lấy từ lần chạy thật của nhóm.

## File nên có trước khi nộp

1. `01-health.png` — `/health` trả `ok: true`, không lộ key.
2. `02-validate-logs.txt` — output cuối của `python scripts/validate_logs.py` (mục tiêu 100/100, tối thiểu 80/100).
3. `03-traces-list.png` — Langfuse có ít nhất 10 traces.
4. `04-trace-waterfall.png` — một trace mở chi tiết, nhìn thấy span `retrieval` và `llm_call`.
5. `05-prompt-versions.png` — prompt `day13-chat` có V1/V2 và labels.
6. `06-prompt-rollback.png` — bằng chứng đổi `production` rồi rollback.
7. `07-log-correlation.json` — nhiều event dùng cùng correlation ID.
8. `08-pii-redaction.json` — log đã che email/phone/card.
9. `09-validate-dashboard.txt` — phải có `HỢP LỆ: 6/6 panel`.
10. `10-dashboard.png` — dashboard đủ latency, traffic, error, cost, token, quality; thấy time range + unit + threshold.
11. `11-challenge-metrics.png` — metric khi chạy challenge `rag_slow`.
12. `12-challenge-trace.png` — trace challenge, span retrieval khoảng 2.5s là bất thường.
13. `13-challenge-log.json` — log cùng correlation ID, có `retrieval_completed.latency_ms` làm bằng chứng.

## Tự sinh evidence text/JSON

Sau khi đã chạy baseline + request PII:

```powershell
python scripts/collect_evidence.py
```

Script tạo các file text/JSON/HTML có thể tự động tạo. Screenshot Langfuse và dashboard vẫn phải chụp từ lần chạy thật.

## Dashboard local để chụp ảnh

```powershell
python scripts/build_dashboard.py
start submission\evidence\10-dashboard.html
```

Chụp màn hình HTML thành `submission/evidence/10-dashboard.png`.
