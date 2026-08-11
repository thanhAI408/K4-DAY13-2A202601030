# CP1 — PII Scrubbing (Thành viên B — Security Engineer)

## Phạm vi
Regex patterns che PII + kiểm chứng log không lộ PII. (Correlation ID và
enrichment thuộc vai trò Logging — không nằm trong phần này.)

## Thay đổi
1. **Kích hoạt processor `scrub_event`** trong pipeline `structlog`
   ([app/logging_config.py](../../app/logging_config.py)) — trước đó bị comment out,
   nghĩa là lớp che PII ở tầng log chưa chạy. Đặt **trước** `JsonlFileProcessor`
   để dữ liệu ghi ra đĩa đã được redact.
2. **Quét đệ quy mọi field chuỗi** (không chỉ `payload`) — không phụ thuộc caller
   đặt PII đúng chỗ; bỏ qua các key định danh (`ts`, `level`, `correlation_id`,
   `user_id_hash`).
3. **Mở rộng regex** ([app/pii.py](../../app/pii.py)): thêm `passport_vn`,
   `address_vn`; sắp lại thứ tự để pattern cụ thể (credit_card, cccd) chạy trước
   pattern số điện thoại, tránh redact một phần.

## Kiểm chứng
### a) End-to-end qua pipeline (kể cả field ngoài `payload`)
Log một record có PII ở field `raw_field` + nested payload → 4 detector độc lập
(email, phone_vn, cccd, credit_card) báo: **PII DETECTED: NONE - clean**.

### b) Load test trên dữ liệu mẫu có PII thật
`data/sample_queries.jsonl` chứa `student@vinuni.edu.vn`, `0987654321`, thẻ test.
Sau `scripts/load_test.py` → `scripts/validate_logs.py`:

```
Potential PII leaks detected: 0
+ [PASSED] PII scrubbing
```

Record thật đã che (từ query có PII):
```json
{"payload": {"message_preview": "... My email is [REDACTED_EMAIL]"}, "event": "request_received", ...}
{"payload": {"message_preview": "Here is my phone [REDACTED_PHONE_VN], ..."}, ...}
{"payload": {"message_preview": "... credit card [REDACTED_CREDIT_CARD]?"}, ...}
```

### c) Unit test
`python -m pytest tests/test_pii.py -q` → **7 passed** (email, 5 định dạng phone VN,
cccd, credit_card, passport, address, và test processor đệ quy). Toàn bộ suite: 27 passed.

## Bàn giao / phụ thuộc
- Điểm validate_logs hiện 30/100 vì các mục **Correlation ID + Enrichment** (vai trò
  Logging) chưa xong trong `app/middleware.py` và `app/main.py`. Khi hoàn thành,
  phần PII đã sẵn sàng đạt tiêu chí ≥80/100.
