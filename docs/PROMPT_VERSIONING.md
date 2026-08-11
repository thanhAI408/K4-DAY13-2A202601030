# Prompt versioning cơ bản

Mục tiêu là chứng minh mỗi request biết chính xác prompt version nào đã dùng và có thể đổi label/rollback có bằng chứng. Không chấm prompt nào “hay hơn”.

## Prompt contract bắt buộc

Prompt tên `day13-chat` và giữ đúng ba biến:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

Ứng dụng fetch theo:

```dotenv
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

## Hai version đề xuất

**Version 1 — baseline + production**

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

**Version 2 — candidate**

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
Answer using the retrieved evidence. Keep the response concise and explain the observability signal when relevant.
```

## Các bước lấy evidence

1. Trong Langfuse tạo V1 với labels `baseline`, `production`.
2. Tạo V2 với label `candidate`.
3. Chạy cùng một input với `LANGFUSE_PROMPT_LABEL=baseline`, sau đó `candidate`.
4. Chụp hai trace có `prompt_name`, `prompt_label`, `prompt_version` khác nhau.
5. Chuyển label `production` sang V2, chạy một request và chụp evidence.
6. Rollback `production` về V1 và chụp evidence.
7. Ghi trace ID + đường dẫn ảnh vào `submission/REPORT.md`.

Nếu Langfuse không khả dụng, app dùng prompt local và ghi `prompt_source=local`/`local-fallback`. Trạng thái fallback **không được dùng làm bằng chứng managed prompt**.
