# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- SLI/SLO liên quan: `latency_p95_ms` (Mục tiêu: 99.5% request có thời gian xử lý ≤ 3000ms trong 28 ngày)
- Điều kiện và thời gian duy trì: `latency_p95 > 3000ms` kéo dài liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng trải nghiệm ứng dụng phản hồi rất chậm, thời gian tải trang kéo dài, có nguy cơ gặp sự cố timeout ở phía giao diện frontend.
- Ba bước kiểm tra đầu tiên:
1. Kiểm tra Traffic & Request Rate (RPS): Quan sát dashboard APM/Prometheus để xác định xem có hiện tượng tăng đột biến lưu lượng truy cập (Traffic Spike) hay không.
2. Kiểm tra Tài nguyên Hạ tầng: Kiểm tra mức độ tiêu thụ CPU, RAM, Network I/O của các Pod/Container đang chạy dịch vụ.
3. Kiểm tra External Dependencies & Database: Phân tích xem độ trễ phát sinh tại code ứng dụng hay do truy vấn CSDL chậm (Slow Queries) hoặc API của dịch vụ bên thứ 3 bị phản hồi chậm.
- Mitigation tạm thời: Thực hiện Scale-out khẩn cấp (tăng số lượng Replica/Pod) để phân tán tải nếu CPU/RAM đang ở mức trần. Bật layer Caching hoặc tăng TTL cache đối với các endpoint thao tác đọc (Read operations). Kích hoạt Rate Limiting hoặc chế độ Graceful Degradation (tạm ngắt các tính năng phụ không thiết yếu) nếu hệ thống bị quá tải.
- Owner: `on-call-engineer`

## Alert 2

- Tên: `elevated_error_rate`
- Severity: `critical`
- SLI/SLO liên quan: `error_rate_pct` (Mục tiêu: 99.0% request thành công, Tỷ lệ lỗi ≤ 2.0% trong 28 ngày)
- Điều kiện và thời gian duy trì: `error_rate_pct > 5` (hoặc vượt ngưỡng cho phép 2%) kéo dài liên tục trong 3 phút.
- Ảnh hưởng tới người dùng: Người dùng liên tục nhận thông báo lỗi (HTTP 5xx, 500 Internal Error, 502 Bad Gateway), các thao tác/giao dịch chính trên hệ thống bị thất bại. Error Budget tiêu tốn rất nhanh.
- Ba bước kiểm tra đầu tiên:
1. Kiểm tra Lịch sử Deploy/Release: Xác định xem có bản cập nhật code, thay đổi cấu hình (config update) hay database migration nào vừa diễn ra trong vòng 15–30 phút qua không.
2. Kiểm tra Application Error Logs: Lọc log lỗi hệ thống theo mã trạng thái 5xx, kiểm tra Stack Trace để xác định nguyên nhân gốc (Unhandled Exception, Database Connection Timeout, Null Pointer Exception,...).
3. Kiểm tra Health Check & Downstream Services: Kiểm tra kết nối tới Database, Cache layer (Redis) cũng như trạng thái phản hồi từ các service phụ thuộc downstream.
- Mitigation tạm thời: Nếu sự cố xuất hiện ngay sau khi deploy: Tiến hành Rollback lập tức về phiên bản build ổn định trước đó. Nếu do mất kết nối hoặc nghẽn dịch vụ phụ thuộc: Kích hoạt Circuit Breaker hoặc điều hướng người dùng sang trang thông báo bảo trì/fallback response. Restart khẩn cấp các Pod/Container bị rơi vào trạng thái Deadlock hoặc tràn bộ nhớ (Out-Of-Memory).
- Owner: `on-call-engineer`

## Alert 3

- Tên: `cost_budget_exceeded`
- Severity: `warning`
- SLI/SLO liên quan: `daily_cost_usd` (Mục tiêu: Chi phí vận hành dưới $2.5/ngày)
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5` (Chi phí tích lũy trong ngày vượt trần ngân sách $2.5).
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp đến trải nghiệm thời gian thực của người dùng cuối, nhưng nguy hại tới ngân sách dự án và có nguy cơ bị Cloud Provider dừng tài nguyên do vượt hạn mức thanh toán.
- Ba bước kiểm tra đầu tiên:
1. Kiểm tra Cloud Billing Dashboard: Phân tích chi tiết dịch vụ nào đang chiếm tỷ trọng chi phí cao nhất (Compute, Outbound Network Egress, Token API của LLM, Storage Reads/Writes).
2. Kiểm tra Auto-scaling & Resource Leaks: Kiểm tra xem số lượng Replica đang scale có bị treo ở mức cực đại không, hoặc có các background worker/job đang chạy lặp vô hạn.
3. Kiểm tra Tần suất Gọi External API: Kiểm tra chỉ số log request sang các nhà cung cấp tính phí theo lượt gọi/token (ví dụ: OpenAI API, Payment Gateways, SMS Services).
- Mitigation tạm thời: Điều chỉnh hạ ngưỡng Max Replicas trên HPA (Horizontal Pod Autoscaler) về hạn mức an toàn. Tạm dừng hoặc hoãn thời gian chạy của các Cronjob / Batch Processing tốn nhiều tài nguyên xử lý. Thắt chặt Rate Limit đối với các API endpoint có chi phí xử lý đắt đỏ.
- Owner: `team-lead`
