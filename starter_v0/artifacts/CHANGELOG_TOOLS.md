# Changelog — Tool Engineer

> Nhật ký thay đổi của vai **Tool Engineer** (Vinh). Ghi lại *cái gì đổi* và
> *tại sao*, để Prompt Engineer / UI / Documenter biết ranh giới và lấy nội dung
> đưa vào `REPORT.md`.
>
> File này **không thay thế** `version_log.csv`. `version_log.csv` ghi thí nghiệm
> prompt/tool-declaration theo version v0–v3; file này ghi thay đổi hạ tầng và
> tool implementation.

---

## 1. Thêm NVIDIA NIM làm model provider

**Vì sao:** nhóm muốn chạy được trên NIM bên cạnh OpenRouter.

NIM dùng surface OpenAI-compatible nên provider chỉ là một subclass mỏng, giống
hệt cách `OpenRouterProvider` được viết.

| File | Thay đổi |
|---|---|
| `providers/nim_provider.py` | **mới** — subclass `OpenAIProvider`, `NVIDIA_API_KEY`, base URL `https://integrate.api.nvidia.com/v1` |
| `providers/__init__.py` | import + nhánh `if name == "nim"` trong `make_provider` |
| `run_eval.py`, `chat.py`, `scripts/preflight_provider.py` | thêm `"nim"` vào `--provider choices` |
| `.env.example` | placeholder `NVIDIA_API_KEY`, comment `NIM_BASE_URL` / `NIM_MODEL` |

Đổi model không cần sửa code: đặt `NIM_MODEL` trong `.env` hoặc truyền `--model`.

**Lưu ý vận hành:** model mặc định hiện tại là bản reasoning-tuned — chính xác
nhưng chậm (~5–10s mỗi call). Với 20 case base eval thì một lần `run_eval` mất
khoảng 4–8 phút. `meta/llama-3.3-70b-instruct` nhanh hơn nếu cần đánh đổi.

---

## 2. Sửa lỗi treo khi gọi provider

**Triệu chứng:** `python scripts/preflight_provider.py --provider nim` đứng im
rất lâu, không báo lỗi cũng không trả kết quả.

**Nguyên nhân:** OpenAI SDK mặc định `timeout=600s` với 2 lần retry. Khi endpoint
không phản hồi, nó chờ tới ~30 phút rồi mới ném lỗi. Không phải "chạy lâu" — là
chờ vô ích.

**Sửa:** `providers/openai_provider.py` nhận thêm `timeout` (mặc định `60.0`) và
`max_retries` (mặc định `2`), truyền xuống client. Áp dụng cho **mọi** provider
dùng surface OpenAI (OpenAI, OpenRouter, NIM).

**Thêm `scripts/diag_provider.py`** — chẩn đoán fail-fast, tách 6 lớp với timeout
ngắn: config → API key → DNS → TCP → chat completion → structured tool calling.
Mỗi lớp hỏng thì in gợi ý xử lý tương ứng (temperature bị từ chối, 401, model id
sai...). Chạy cái này **trước** `preflight_provider.py` mỗi khi nghi ngờ.

```bash
python scripts/diag_provider.py --provider nim
```

---

## 3. Bốn tool mới — "Sổ tay nghiên cứu"

**Câu chuyện:** agent là trợ lý nghiên cứu duy trì một sổ tay cá nhân. Mỗi tool
trả lời **đúng một câu hỏi nghiệp vụ** và trả về **kết luận**, không phải dữ liệu thô.

| Tool | Câu hỏi nghiệp vụ | Trả về | Nguồn | Key |
|---|---|---|---|---|
| `define` | "X nghĩa là gì?" | `definition` — 1–2 câu sẵn sàng dán vào sổ | Wikipedia REST | không |
| `scholar` | "Công trình nào về X đã được công nhận?" | `verdict` + `most_cited` | OpenAlex | không |
| `note_write` | "Mở sổ mới cho chủ đề này" | tạo `notes/<slug>.md` | filesystem | không |
| `note_append` | "Ghi phát hiện này vào sổ đã có" | bổ sung mục có timestamp | filesystem | không |

Luồng demo: `define`/`scholar` (thu thập) → `note_write` (mở sổ) → `note_append`
(bổ sung dần).

Mỗi tool có đủ 5 thành phần bắt buộc: `TOOL.md`, `tool.py`, đăng ký trong
`tools/__init__.py`, declaration trong `artifacts/tools.yaml`, và quicktest.
Thêm `tools/_notes.py` chứa helper dùng chung cho hai tool note (slug ổn định để
`note_append` tìm lại được note mà `note_write` đã tạo).

### Ba hành vi cố ý thiết kế, không phải bug

1. **`note_write` từ chối ghi đè** note đã tồn tại, và báo lỗi chỉ sang
   `note_append`. Sổ nghiên cứu không được phép mất dữ liệu cũ.
2. **`note_append` không tự tạo note.** Không tìm thấy thì báo lỗi **kèm danh
   sách note đang có**, để agent tự chọn `note_write` hoặc `clarify`.
3. **`define` gặp thuật ngữ mơ hồ thì báo lỗi thay vì đoán.** Ví dụ "Mercury"
   (hành tinh? nguyên tố? thần thoại?) → ép agent phải `clarify`.

### Confirmation boundary

`note_write` và `note_append` đều **có side effect**. Mặc định `confirmed=false`
→ không ghi gì, trả `status="needs_confirmation"` kèm mô tả việc sẽ làm. Agent
phải gọi `clarify` với `response_type="yes_no"` trước, người dùng đồng ý rồi mới
gọi lại với `confirmed=true`. Hành vi này khớp với `send` có sẵn trong starter.

---

## 4. Sửa lỗi chất lượng của `scholar` (quan trọng)

**Triệu chứng:** quicktest báo PASS nhưng kết quả sai chủ đề.

```
Most-cited work on 'retrieval augmented generation':
  'SciPy 1.0: fundamental algorithms for scientific computing in Python' (2020, 38673 cites)
```

**Nguyên nhân:** khi truyền `sort=cited_by_count:desc`, OpenAlex **vứt bỏ toàn bộ
xếp hạng liên quan** và trả về bài được trích dẫn nhiều nhất có chứa bất kỳ từ
nào trong query. Đúng về số liệu, sai hoàn toàn về chủ đề.

**Sửa — xếp hạng hai bước:**

1. Lấy pool ứng viên **liên quan về chủ đề** qua `filter=title_and_abstract.search:<query>`
   (chặt hơn search toàn văn), over-fetch `max(limit*5, 25)` kết quả.
2. **Sắp pool đó theo `cited_by_count` tại chỗ**, rồi cắt lấy `limit`.

Nếu lọc title/abstract không ra kết quả, tự lùi về search rộng hơn. Query cũng
được làm sạch ký tự `, | :` vì đó là dấu phân cách filter của OpenAlex.

**Chống tái phát:** thêm assertion `scholar:top_hit_is_on_topic` vào quicktest —
tiêu đề của kết quả đầu phải chia sẻ ít nhất một từ khoá với query.

---

## 5. Sửa hai lỗi trong chính quicktest

- `define:empty_term_rejected` dùng `term=bad or "AI"`, mà `"" or "AI"` → `"AI"`,
  nên case term rỗng **chưa bao giờ được test**. Tách thành hai check tường minh.
- `define:typo_fallback` dùng chuỗi méo phi thực tế (`retreival augmentd generaton`).
  Đổi sang typo thực tế hơn, **và** cải thiện tool: `define` giờ dùng
  `srinfo=suggestion` của Wikipedia, nên typo nặng không có hit vẫn resolve được
  qua gợi ý "did you mean".

---

## 6. Ranh giới routing → nguyên liệu cho `eval_group.json`

Bốn tool này được thiết kế để tạo ranh giới routing rõ ràng với tool có sẵn:

| Ranh giới | `failure_type` |
|---|---|
| `define` vs `lookup` — khái niệm nền vs "mới nhất" | `wrong_tool` |
| `scholar` vs `papers` — peer-reviewed/trích dẫn vs preprint arXiv | `wrong_tool` |
| `note_write` vs `note_append` — tạo mới vs bổ sung | `wrong_tool` |
| hai tool note — `confirmed=true` khi chưa `clarify` | `wrong_boundary` |
| `note_append` khi không rõ note nào | `missing_info` |
| `scholar` với `min_year` chặn mất công trình kinh điển | `wrong_arg_value` |

---

## ⚠ Việc nhóm cần quyết trước khi chạy eval tiếp

Thêm 4 tool vào `tools.yaml` **làm thay đổi routing của toàn bộ agent**. Bốn run
`v0`–`v3` hiện có được chạy với **10 tool**; sau thay đổi này agent có **14 tool**,
nên bảng metric cũ không còn so sánh trực tiếp được nữa.

Chọn một:

- **A. Chạy lại `v0`–`v3` với 14 tool.** Sạch sẽ, nhất quán. Tốn ~20–30 phút với
  model reasoning hiện tại.
- **B. Giữ run cũ, comment khối tool mới khi chạy base eval**, chỉ bật lên cho
  `eval_group` và demo. Nhanh hơn nhiều. Hướng dẫn nằm ngay trong comment đầu
  khối `TEAM-BUILT TOOLS` ở cuối `artifacts/tools.yaml`.

---

## Ghi chú cho các vai khác

**Prompt Engineer**

- Mình **chỉ append** vào cuối `tools.yaml`, không đụng 10 declaration cũ. Toàn bộ
  phần trên khối `TEAM-BUILT TOOLS` vẫn là của bạn.
- Muốn sửa description 4 tool mới thì cứ sửa, chỉ cần báo để mình sync lại `TOOL.md`.
- **Bằng chứng cho luận điểm "tools.yaml chưa được tối ưu":** preflight với câu
  *"Tweet mới nhất của Sam Altman là gì?"* cho ra `social_search(query="Sam Altman")`,
  trong khi đáng lẽ phải là `timeline(screenname="sama")`. Đây đúng là case
  `R01_user_tweets_routing`. Nguyên nhân là `timeline` vẫn còn mô tả
  `"Lấy các bài đăng gần đây."` — quá mơ hồ để phân biệt với `social_search`.
- `version_log.csv` hiện vẫn **trống, chỉ có header**. Đề bài bắt buộc ghi đủ
  hypothesis / hash / metric before-after cho v0–v3.

**DevOps & Documenter**

- Repo đang có **CRLF/LF mismatch**: 64 file hiện `M` nhưng
  `git diff --ignore-all-space` ra rỗng — không có thay đổi nội dung thật nào.
  Chạy trước khi commit đầu tiên, nếu không sẽ đẻ diff giả ~8.600 dòng:

  ```bash
  git config core.autocrlf true
  git add --renormalize .
  ```

- `notes/` đã được thêm vào `.gitignore` (do `note_write`/`note_append` sinh ra
  khi demo).
- `OPENALEX_MAILTO` trong `.env.example` là **tuỳ chọn**, chỉ để vào polite pool
  của OpenAlex. Không có vẫn chạy bình thường.

**UI/UX Developer**

- Hai tool note trả `status="needs_confirmation"` ở lượt đầu. UI nên hiển thị
  trạng thái này khác với lỗi — đây là luồng bình thường, không phải failure.
- `scholar` trả `verdict` (một dòng kết luận) tách khỏi `works[]` (bằng chứng).
  Hiển thị `verdict` nổi bật sẽ demo tốt hơn là đổ nguyên mảng.

---

## Cách chạy lại bằng chứng

```bash
# Provider hoạt động
python scripts/diag_provider.py --provider nim
python scripts/preflight_provider.py --provider nim

# Bốn tool mới (bỏ --offline để test cả define + scholar qua mạng)
python scripts/quicktest_new_tools.py
```
