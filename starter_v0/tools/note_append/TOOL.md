---
name: note_append
track: team_new
kind: action
provider: local filesystem
requires_env: []
inputs: [topic, entry, section, confirmed]
outputs: [status, path, section]
side_effect: true
---
# note_append

**Câu hỏi nghiệp vụ:** *"Ghi phát hiện mới này vào mục ghi chú tôi đã có."*

Bổ sung một mục vào `notes/<slug>.md` đã tồn tại. **Có side effect** — sửa file thật.

## Confirmation boundary

Giống `note_write`:

- `confirmed=false` (mặc định) → **không sửa gì**, trả `status="needs_confirmation"`
  kèm `would_append`.
- `confirmed=true` → mới thực sự ghi.

Phải `clarify` với `response_type="yes_no"` trước.

## Phân biệt với `note_write`

| Tình huống | Tool đúng |
|---|---|
| Chủ đề chưa có ghi chú | `note_write` |
| Chủ đề **đã có** ghi chú | `note_append` |

Tool này **không bao giờ tự tạo note mới**. Nếu không tìm thấy, nó báo lỗi kèm
**danh sách note đang có** — agent dùng danh sách đó để hoặc gọi `note_write`,
hoặc `clarify` hỏi người dùng ý là note nào.

## Khi nào KHÔNG dùng

- Chủ đề hoàn toàn mới, chưa có sổ → `note_write`.
- Người dùng nói mơ hồ "lưu vào ghi chú của tôi" mà đang có nhiều note và không
  rõ note nào → `clarify` hỏi trước, đừng đoán.

## Arguments

| Arg | Default | Ghi chú |
|---|---|---|
| `topic` | — | Bắt buộc. Phải khớp `topic` đã dùng khi tạo note (slug sinh ra ổn định nên gõ lại tự nhiên là khớp). |
| `entry` | — | Bắt buộc. Nội dung markdown cần thêm. |
| `section` | `Findings` | Tiêu đề `##` cho mục mới. Ví dụ `Sources`, `Open questions`, `Related work`. |
| `confirmed` | `false` | Chỉ `true` SAU KHI người dùng xác nhận. |

## Output

- Chưa xác nhận: `{"status": "needs_confirmation", "would_append": {...}}`
- Đã ghi: `{"status": "appended", "note": "<slug>", "section": "...", "bytes": N}`
- Không tìm thấy note: lỗi kèm `Existing notes: [...]` để agent xử lý tiếp.

Mỗi mục được đóng dấu thời gian UTC, nên sổ đọc được như một nhật ký nghiên cứu.
