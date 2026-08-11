# Alert rules và runbook

Các alert bên dưới dựa trên triệu chứng người dùng hoặc SLO. Khi xử lý, đi theo
luồng dashboard → trace → log và ghi lại correlation ID của request đại diện.

## Alert 1

- Tên: `api_latency_slo_breach`
- Severity: `critical`
- SLI/SLO liên quan: `latency_p95_ms`, P95 ≤ 3000 ms trong ít nhất 99.5% cửa sổ 5 phút.
- Điều kiện và thời gian duy trì: `p95(response_sent.latency_ms) > 3000` trong 5 phút.
- Ảnh hưởng tới người dùng: chat phản hồi chậm hoặc timeout, đặc biệt ở tail latency.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel **Latency** trong khoảng thời gian alert và xác nhận P95 cùng traffic.
  2. Mở một trace chậm nhất, so sánh waterfall của `rag.retrieve` và `llm.generate`.
  3. Tra log `api/response_sent` theo `correlation_id`, kiểm tra `latency_ms`, `feature`, `model` và incident đang bật.
- Mitigation tạm thời: tắt incident/feature gây chậm nếu đã xác định, giảm concurrency hoặc chuyển traffic sang model/config ổn định; sau đó theo dõi P95 trong ít nhất 15 phút.
- Owner: SRE

## Alert 2

- Tên: `api_error_rate_slo_breach`
- Severity: `critical`
- SLI/SLO liên quan: `error_rate_pct` ≤ 2%.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` trong 5 phút.
- Ảnh hưởng tới người dùng: request thất bại, nhận lỗi 5xx hoặc không có câu trả lời hợp lệ.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel **Errors**, đối chiếu `request_failed` với tổng `request_received` và phân nhóm `error_type`.
  2. Chọn correlation ID của lỗi mới nhất và mở log đầy đủ, gồm exception type/message đã được scrub.
  3. Mở trace tương ứng để xác định lỗi nằm ở RAG, LLM hay middleware/transport.
- Mitigation tạm thời: rollback prompt/config vừa triển khai, tắt dependency lỗi hoặc bật fallback; nếu lỗi còn tiếp diễn thì giới hạn traffic và escalate cho owner API.
- Owner: API/SRE

## Alert 3

- Tên: `api_daily_cost_budget_breach`
- Severity: `warning`
- SLI/SLO liên quan: tổng `cost_usd` trong rolling 24 giờ ≤ 2.5 USD.
- Điều kiện và thời gian duy trì: `sum(response_sent.cost_usd) > 2.5` trong rolling 24 giờ.
- Ảnh hưởng tới người dùng: có nguy cơ throttling hoặc phải giảm chất lượng/model để giữ ngân sách.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel **Cost** và **Tokens**, so sánh cost theo model với traffic và token usage.
  2. Kiểm tra trace gần thời điểm tăng chi phí, tập trung vào `prompt_version`, số token và số lần gọi tool/RAG.
  3. Tra log `api/response_sent` theo `model`, `feature`, `cost_usd` để tìm nhóm request bất thường.
- Mitigation tạm thời: giới hạn token/output, chọn model tiết kiệm hơn và tạm dừng workload không ưu tiên; rollback prompt nếu prompt mới làm tăng token.
- Owner: FinOps/SRE
