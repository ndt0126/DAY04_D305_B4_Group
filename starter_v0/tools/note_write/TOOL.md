---
name: note_write
track: team_new
kind: action
provider: local filesystem
requires_env: []
inputs: [topic, content, confirmed]
outputs: [status, path, note]
side_effect: true
---
# note_write

**Câu hỏi nghiệp vụ:** *"Mở một mục ghi chú mới cho chủ đề này."*

Tạo file `notes/<slug>.md`. **Có side effect** — ghi file thật lên đĩa.

## Confirmation boundary

- `confirmed=false` (mặc định) → **không tạo gì**, trả `status="needs_confirmation"`
  kèm `would_create` để agent trình bày cho người dùng duyệt.
- `confirmed=true` → mới thực sự tạo file.

Agent **phải** gọi `clarify` với `response_type="yes_no"` trước, người dùng đồng ý
rồi mới gọi lại với `confirmed=true`. Tự đặt `confirmed=true` ngay lượt đầu là
vi phạm boundary.

## Phân biệt với `note_append`

| Tình huống | Tool đúng |
|---|---|
| Chủ đề chưa có ghi chú nào | `note_write` |
| Chủ đề **đã có** ghi chú, muốn bổ sung | `note_append` |

`note_write` **cố tình từ chối ghi đè**. Nếu note đã tồn tại, nó báo lỗi và chỉ
sang `note_append`. Đây là hành vi thiết kế, không phải bug — sổ nghiên cứu không
được phép mất dữ liệu cũ.

## Khi nào KHÔNG dùng

- Muốn thêm vào ghi chú đã có → `note_append`.
- Người dùng chỉ muốn xem kết quả, không nói gì đến việc lưu → dừng ở `format`.
- Muốn gửi ra ngoài (Telegram/channel) → dùng `send`.

## Arguments

| Arg | Default | Ghi chú |
|---|---|---|
| `topic` | — | Bắt buộc. Sinh slug ổn định (bỏ dấu tiếng Việt, cắt 60 ký tự) để `note_append` tìm lại được. |
| `content` | — | Bắt buộc. Nội dung markdown cho phần Overview, thường ghép từ `define` / `scholar` / `format`. |
| `confirmed` | `false` | Chỉ `true` SAU KHI người dùng xác nhận rõ ràng. |

## Output

- Chưa xác nhận: `{"status": "needs_confirmation", "would_create": {...}}`
- Đã tạo: `{"status": "created", "note": "<slug>", "path": "notes/<slug>.md", "bytes": N}`
- Trùng tên: lỗi kèm thông điệp chỉ sang `note_append`.

> `notes/` đã nằm trong `.gitignore`.
