---
name: define
track: team_new
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [term, lang, max_sentences]
outputs: [definition, url, resolved_title]
side_effect: false
---
# define

**Câu hỏi nghiệp vụ:** *"Thuật ngữ này nghĩa là gì, cho tôi một câu để ghi vào sổ?"*

Trả về **một định nghĩa ngắn gọn đã sẵn sàng dán vào ghi chú** — không phải cả
bài viết, không phải danh sách kết quả tìm kiếm. Không cần API key.

## Khi nào dùng

- "X là gì?", "định nghĩa X", "giải thích khái niệm X".
- Cần một câu chú thích chuẩn cho thuật ngữ trước khi ghi vào sổ nghiên cứu.
- Cần bối cảnh nền về một người/tổ chức/sự kiện đã ổn định theo thời gian.

## Khi nào KHÔNG dùng

- Câu hỏi có yếu tố thời sự: "mới nhất", "hôm nay", "tuần này", "vừa ra mắt"
  → dùng `lookup` với `topic="news"`. Bách khoa toàn thư không phải nguồn tin.
- Cần công trình nghiên cứu, paper, trích dẫn → dùng `scholar` hoặc `papers`.
- Đã có URL cụ thể cần đọc → dùng `fetch`.

## Arguments

| Arg | Default | Ghi chú |
|---|---|---|
| `term` | — | Bắt buộc. Gõ sai chính tả vẫn được vì tool có fallback search. |
| `lang` | `en` | Chỉ `en` hoặc `vi`. Chủ đề Việt Nam dùng `vi`; thuật ngữ kỹ thuật quốc tế dùng `en` vì nội dung đầy đủ hơn. |
| `max_sentences` | `2` | 1–5. Tăng lên khi cần định nghĩa dài hơn cho phần mở đầu ghi chú. |

## Hành vi

1. Gọi thẳng endpoint summary với `term`.
2. Nếu 404 → tìm qua search API rồi gọi lại với title khớp nhất.
3. Nếu trúng trang disambiguation → **báo lỗi** kèm gợi ý hỏi lại người dùng cho
   cụ thể hơn. Đây là hành vi cố ý: agent nên `clarify` chứ không đoán bừa.

## Output

`definition` (kết luận chính), kèm `resolved_title`, `short_description`, `url`,
`source`. Dùng `definition` + `url` để dựng một mục ghi chú có dẫn nguồn.
