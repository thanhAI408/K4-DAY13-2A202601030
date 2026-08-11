# Alert và Runbook — Day 13

Các alert dưới đây dựa trên triệu chứng/SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- **Tên:** `high_latency_p95`
- **Severity:** `warning`
- **SLI/SLO:** P95 latency ≤ 3000 ms.
- **Điều kiện:** P95 > 3000 ms liên tục 5 phút.
- **Ảnh hưởng:** người dùng cảm thấy API phản hồi chậm hoặc timeout.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở panel Latency P50/P95/P99 để xác nhận thời điểm và mức tăng.
  2. Mở một trace chậm trong khoảng đó, so sánh span `retrieval` và `llm_call`.
  3. Tìm các log cùng `correlation_id`, kiểm tra `retrieval_completed.latency_ms` và tổng latency.
- **Mitigation tạm thời:** giảm tải, cache/timeout retrieval, hoặc rollback thay đổi vừa triển khai; với practice thì tắt incident sau khi thu evidence.
- **Owner:** `on-call-engineer`.

## Alert 2

- **Tên:** `elevated_error_rate`
- **Severity:** `critical`
- **SLI/SLO:** error rate ≤ 2%.
- **Điều kiện:** error rate > 2% liên tục 3 phút.
- **Ảnh hưởng:** request thất bại, người dùng không nhận được câu trả lời.
- **Ba bước kiểm tra đầu tiên:**
  1. Xem error breakdown để xác định loại lỗi chiếm ưu thế.
  2. Mở trace lỗi và xác định span thất bại.
  3. Dùng cùng `correlation_id` để tìm `request_failed`/`retrieval_failed` và `error_type` trong log.
- **Mitigation tạm thời:** rollback cấu hình mới, thêm timeout/retry có giới hạn hoặc fallback/circuit breaker cho dependency lỗi.
- **Owner:** `on-call-engineer`.

## Alert 3

- **Tên:** `cost_budget_exceeded`
- **Severity:** `warning`
- **SLI/SLO:** daily cost ≤ 2.5 USD.
- **Điều kiện:** tổng cost trong ngày > 2.5 USD.
- **Ảnh hưởng:** không nhất thiết làm người dùng lỗi ngay nhưng có nguy cơ vượt ngân sách.
- **Ba bước kiểm tra đầu tiên:**
  1. So sánh cost với traffic để biết chi phí tăng do nhiều request hay do từng request đắt hơn.
  2. Kiểm tra `tokens_in`/`tokens_out`, model và prompt version trong trace/log.
  3. Tìm request có output token bất thường và kiểm tra thay đổi prompt/model gần nhất.
- **Mitigation tạm thời:** giới hạn output, giảm context không cần thiết, rate-limit, hoặc dùng model phù hợp chi phí hơn.
- **Owner:** `team-lead`.
