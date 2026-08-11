# Trạng thái bản nộp tĩnh

Các phần đã chuẩn bị sẵn để commit:

- Source hoàn thiện TODO chính của logging/correlation/PII.
- Tracing + prompt metadata.
- Dashboard contract 6 panel.
- SLO + alert rules + runbook.
- Scripts dashboard/evidence/pre-submit.
- Tests bổ sung.
- Report đã điền toàn bộ nội dung có thể xác định từ source/challenge.
- Danh sách 5 thành viên và phân vai.

Các phần **không thể tạo hợp lệ nếu không chạy**:

- validate_logs score thật;
- ≥10 Langfuse trace thật;
- trace waterfall screenshot;
- prompt label switch/rollback screenshot;
- PII/correlation log sinh từ runtime;
- dashboard screenshot từ dữ liệu runtime;
- challenge metric/trace/log thật;
- commit SHA và link commit/PR thật.

Không thêm `.env` hoặc secret vào Git. Không sửa `config/challenge.json`.
