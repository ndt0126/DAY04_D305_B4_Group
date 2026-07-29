---
name: scholar
track: team_new
kind: live_api
provider: OpenAlex
requires_env: []
inputs: [query, min_year, limit]
outputs: [verdict, most_cited, works]
side_effect: false
---
# scholar

**Câu hỏi nghiệp vụ:** *"Về chủ đề này, công trình nào đã được giới học thuật công nhận nhất?"*

Xếp hạng tài liệu học thuật theo **số lượt trích dẫn** qua OpenAlex, nên kết quả
đầu tiên là công trình nền tảng của lĩnh vực chứ không phải bài mới nhất.
Không cần API key.

## Phân biệt với `papers` (built-in)

Đây là ranh giới quan trọng nhất, đừng nhầm:

| | `papers` | `scholar` |
|---|---|---|
| Nguồn | Chỉ arXiv | Mọi nhà xuất bản (OpenAlex) |
| Loại | Preprint, chưa bình duyệt | Đã xuất bản, có bình duyệt |
| Sắp xếp | Liên quan / ngày nộp | **Số trích dẫn** |
| Trả lời | "Có gì mới trên arXiv?" | "Cái gì đã được công nhận?" |

## Khi nào dùng

- "Paper kinh điển về X là gì?", "công trình nền tảng của X".
- Cần bằng chứng có sức nặng học thuật (trích dẫn, tạp chí/hội nghị) để dẫn nguồn.
- Cần tài liệu ngoài arXiv: y học, khoa học xã hội, kỹ thuật truyền thống.

## Khi nào KHÔNG dùng

- "Preprint mới nhất trên arXiv" → dùng `papers`.
- Cần đọc **toàn văn** một paper arXiv cụ thể → dùng `paper_text`.
- Chỉ cần định nghĩa khái niệm → dùng `define`.
- Tin tức, blog, thông cáo báo chí → dùng `lookup`.

## Arguments

| Arg | Default | Ghi chú |
|---|---|---|
| `query` | — | Bắt buộc. Từ khoá chủ đề, không phải tên tác giả. |
| `min_year` | *(không lọc)* | Chỉ đặt khi người dùng giới hạn thời gian ("từ 2020 trở lại đây"). Lưu ý: lọc năm gần sẽ **loại mất** công trình kinh điển. |
| `limit` | `5` | Kẹp trong 1–25. |

## Cách xếp hạng (quan trọng)

Xếp hạng đi **hai bước**, không phải một:

1. Hỏi OpenAlex lấy một pool ứng viên **liên quan về chủ đề**, lọc theo
   `title_and_abstract.search` (chặt hơn search toàn văn).
2. **Sắp pool đó theo số trích dẫn tại chỗ**, rồi cắt lấy `limit`.

Lý do: nếu bảo thẳng OpenAlex `sort=cited_by_count:desc`, nó **vứt bỏ toàn bộ
xếp hạng liên quan** và trả về bài được trích dẫn nhiều nhất có chứa bất kỳ từ
nào trong query. Query "retrieval augmented generation" khi đó trả về bài SciPy
1.0 (38.673 trích dẫn) — đúng về số liệu, sai hoàn toàn về chủ đề.

Nếu lọc title/abstract không ra kết quả nào, tool tự lùi về search rộng hơn.

## Output

- `verdict` — **kết luận một dòng**: công trình được trích dẫn nhiều nhất là gì.
- `most_cited` — object đầy đủ của công trình đó.
- `works[]` — `title`, `authors`, `year`, `venue`, `cited_by_count`, `doi`, `url`, `is_open_access`.
- `total_found` — tổng số kết quả khớp trong OpenAlex.

`url` ưu tiên link open-access nếu có, không thì fallback về DOI.

## Ghi chú vận hành

Tool gửi kèm `mailto` để vào "polite pool" của OpenAlex (nhanh và ổn định hơn).
Lấy từ `OPENALEX_MAILTO`, không có thì fallback `ARXIV_USER_AGENT`. Không bắt buộc.
