# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: B4
- Members: 

Nguyễn Đức Trung - 2A202601725 - Agent Logic Developer

Nguyễn Tuấn Nam - 2A2026020398 * -  UI/UX Developer

Nguyễn Quang Vinh - 2A202601049 - Tool Engineer

Lại Duy Đông  - 2A202601913 - Prompt Engineer & Evaluato

Đinh Quang Minh - 2A202601347 - DevOps & Documenter
- Provider/model: NVIDIA NIM

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Agent nghiên cứu thông tin hỗ trợ người dùng tự động tìm kiếm và tổng hợp tin tức trên web cũng như trên các bài viết mạng xã hội (Twitter). Nó có khả năng tự động xử lý song song các truy vấn, hỏi lại người dùng một cách thông minh khi thiếu thông tin cần thiết, đồng thời luôn yêu cầu xác nhận bảo mật trước khi thực thi các tác vụ ghi hoặc gửi dữ liệu.


**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL:

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc yêu cầu xác nhận hành động | không |
| timeline | Lấy các bài đăng gần đây của một tài khoản Twitter | không |
| social_search | Tìm kiếm bài đăng theo từ khóa trên mạng xã hội Twitter | không |
| lookup | Tra cứu thông tin trên internet (web search) | không |
| fetch | Lấy nội dung văn bản từ một địa chỉ URL cụ thể | không |
| format | Trình bày các nguồn thông tin đã thu thập thành markdown digest | không |
| send | Gửi văn bản báo cáo/digest lên Telegram channel | không |
| policy | Tìm kiếm trong tài liệu quy định nội bộ của công ty | không |
| papers | Tìm kiếm bài báo khoa học preprint trên arXiv | không |
| paper_text | Tải PDF arXiv và trích xuất text từ bài báo | không |
| define | Trả về định nghĩa ngắn gọn của thuật ngữ từ bách khoa toàn thư | có (Tool Engineer viết) |
| scholar | Tìm kiếm bài báo học thuật đã công bố sắp xếp theo số trích dẫn | có (Tool Engineer viết) |
| note_write | Tạo mới một sổ tay lưu trữ ghi chú tại notes/<slug>.md | có (Tool Engineer viết) |
| note_append | Bổ sung nội dung nghiên cứu mới vào một sổ tay đã tồn tại | có (Tool Engineer viết) |


## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. **"Định nghĩa thuật ngữ 'Large Language Model' giúp mình."** (Kiểm tra tool mới `define` định nghĩa thuật ngữ chính xác thay vì dùng lookup).
2. **"Tìm kiếm các bài báo khoa học đã được peer-review và trích dẫn nhiều nhất về 'Adam optimizer'."** (Kiểm tra tool mới `scholar` tìm các paper đã công bố uy tín thay vì preprint papers arXiv).
3. **"Tìm trên web tin AI hôm nay và tìm thêm tweet về AI."** (Kiểm tra khả năng gọi song song đồng thời hai tool `lookup` và `social_search` trong 1 turn).
4. **"Mở sổ tay mới nghiên cứu về chủ đề 'Quantum Computing' với nội dung tổng quan."** (Kiểm tra guardrail bảo mật yêu cầu xác nhận `yes_no` qua `clarify` trước khi tạo file mới).
5. **"Lấy 10 tweet mới nhất của Elon Musk"** (Kiểm tra ánh xạ tự động từ tên người dùng thường sang handle `elonmusk` trên Twitter).


## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Hỏi tìm tin tức và bài đăng Twitter cùng lúc | `lookup(query="AI", topic="news", timeframe="day")` và `social_search(query="AI")` chạy song song | Ở bản baseline, model có xu hướng chỉ chạy 1 trong 2 nguồn hoặc gộp query sai. Bản v3 gọi song song và phân phối tham số chuẩn xác. | `runs/v3_B_base_openrouter_20260729T102341228627.json` (Case R13) |
| 2. Ghi chép phát hiện vào sổ tay mới | `clarify(response_type="yes_no")` -> `note_write(topic="Quantum Computing", content="...", confirmed=true)` | Đảm bảo tính an toàn dữ liệu; model buộc phải hỏi người dùng đồng ý trước khi thực hiện ghi file xuống đĩa (side effect). | `runs/v3_B_group_openrouter_20260729T112745081010.json` (Case G08) |
| 3. Chuyển đổi công cụ tìm kiếm trong hội thoại | `timeline(screenname="sama")` -> `lookup(query="OpenAI", topic="news")` (không gọi lại `social_search`) | Khả năng ghi nhớ lịch sử hội thoại nhiều lượt. Khi người dùng ra lệnh "Bỏ Twitter, chuyển sang tìm tin tức trên web", model loại bỏ hoàn toàn các tool mạng xã hội. | `runs/v3_B_base_openrouter_20260729T102341228627.json` (Case M06) |
| 4. Xử lý câu hỏi thiếu nguồn dẫn URL | `clarify(response_type="text", question="...")` | Khi người dùng yêu cầu "Tóm tắt bài viết này giúp mình" nhưng không kèm link, model không tự đoán bừa mà dừng lại hỏi xin URL. | `runs/v3_B_base_openrouter_20260729T102341228627.json` (Case R11) |


---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | system_prompt.md baseline | Initial default prompt run behavior check | accuracy | N/A | 14/20 (70%) | `runs/v0_B_base_openrouter_20260729T101456385781.json` |
| v1 | system_prompt.md (out-of-scope & confirmation rules) | Strict rules prevent model from guessing or calling tools out-of-scope | accuracy | 14/20 (70%) | 14/20 (70%) | `runs/v1_B_base_openrouter_20260729T101902364963.json` |
| v2 | system_prompt.md (name mapping & multiturn context) | Direct mapping avoids clarify calls and enforces history context switching | accuracy | 14/20 (70%) | 19/20 (95%) | `runs/v2_B_base_openrouter_20260729T102303606322.json` |
| v3 | system_prompt.md (enforce clarify parameters) | Enforcing explicit parameter values resolves final formatting mismatches | accuracy | 19/20 (95%) | 20/20 (100%) | `runs/v3_B_base_openrouter_20260729T102341228627.json` |


## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | `lookup(query="tích phân x^2", ...)` | Baseline model tự động đoán và gọi tool để giải toán tích phân thay vì từ chối. | Cấu hình luật từ chối nghiêm ngặt các chủ đề ngoài nghiên cứu (như giải toán/coding) trong system prompt. |
| `R12_confirm_before_send` | `wrong_boundary` | `send(text="...")` | Model tự ý gửi tin nhắn Telegram luôn mà không hỏi xin xác nhận. | Đưa ra quy tắc: Bắt buộc hỏi clarify với `response_type="yes_no"` trước khi thực hiện các tool có side effect (write/send). |
| `R11_missing_url` | `missing_info` | `clarify(question="...")` (no response_type) | Model hỏi lại thiếu tham số `response_type="text"` (dùng default của schema). | Ép buộc model luôn cung cấp giá trị cụ thể cho đối số `response_type` khi gọi tool clarify. |
| `M06_switch_tool` | `wrong_tool` | `lookup(...)` + `social_search(...)` | Khi người dùng bảo chuyển từ Twitter sang tin tức web, model vẫn giữ cả 2 tool. | Cập nhật luật multiturn context để model phân tích chính xác lịch sử chat và lệnh phủ định/thay đổi tool của người dùng. |


## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_define_concept` | Tra cứu định nghĩa cơ bản nền tảng | `define(term="Large Language Model")` | PASS |
| `G02_scholar_vs_papers` | Tìm công trình peer-review xếp hạng theo trích dẫn | `scholar(query="Adam optimizer")` | PASS |
| `G03_note_write_clarify` | Yêu cầu confirm khi tạo sổ tay mới | `clarify(response_type="yes_no")` | PASS |
| `G04_note_append_missing_topic`| Hỏi lại khi không rõ ghi nội dung vào sổ tay nào | `clarify(response_type="text")` | PASS |
| `G05_out_of_scope_cooking` | Không gọi tool với chủ đề ẩm thực nấu ăn | No tool call (Từ chối khéo léo) | PASS |
| `G06_define_disambiguate` | Giải nghĩa từ mơ hồ qua nhiều lượt hội thoại | `define(term="Mercury (element)")` | PASS |
| `G07_scholar_min_year` | Giới hạn thời gian công bố tài liệu học thuật | `scholar(query="Transformer", min_year=2020)` | PASS |
| `G08_note_write_confirm_yes` | Tạo sổ ghi chép sau khi người dùng đồng ý | `note_write(topic="Quantum Computing", confirmed=true)` | PASS |
| `G09_note_append_clarify_name` | Hỏi xác nhận trước khi lưu đè/ghi thêm vào sổ | `clarify(response_type="yes_no")` | PASS |
| `G10_note_append_confirm_yes` | Thực thi ghi thêm vào sổ sau khi đồng ý | `note_append(topic="Large Language Models", entry="Llama 3 8B", confirmed=true)` | PASS |


## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| 1. Tìm tin tức AI và Tweet song song | v3 | `lookup(query="AI", topic="news", timeframe="day")`, `social_search(query="AI", limit=5)` | `transcripts/baseline_openai_20260729T104820195866.transcript.json` | Thành công thu thập cả hai nguồn và tự động gọi format để hiển thị kết quả cho người dùng. |
| 2. Hỏi xác nhận lưu sổ tay | v3 | `clarify(question="Bạn có xác nhận muốn tạo ghi chú mới không?", response_type="yes_no")` -> `note_write(topic="...", content="...", confirmed=true)` | `transcripts/baseline_openai_20260729T113841969903.transcript.json` | Ngăn chặn việc tự ý thay đổi dữ liệu khi chưa được xác nhận; model hỏi lại chuẩn xác. |
| 3. Sửa đổi ý kiến giữa chừng | v3 | `timeline(screenname="sama")` -> `lookup(query="OpenAI", topic="news")` | `transcripts/baseline_openai_20260729T113208019825.transcript.json` | Chuyển đổi công cụ tìm kiếm mượt mà từ timeline Twitter sang web search theo yêu cầu. |


## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `tools/define/` | Định nghĩa chuẩn xác khái niệm "Large Language Model" trực tiếp từ bách khoa toàn thư mà không cần qua google search thô. | Giới hạn `max_sentences` từ 1-5 để tránh bài viết quá dài làm tràn context window. |
| Optional built-in | `tools/send/` | Gửi thành công bản tin tổng hợp lên Telegram channel sau khi người dùng gõ xác nhận Đồng ý. | Cần cài đặt token bảo mật và bắt buộc hỏi ý kiến người dùng yes/no qua `clarify` trước khi gửi đi. |
| Bonus: tool mới thứ 4 trở đi | `tools/note_write/`, `tools/note_append/` | Tự động tạo file markdown `notes/<slug>.md` ghi chép và bổ sung các phát hiện nghiên cứu học thuật của nhóm. | Chỉ được phép tạo/ghi đè file khi cờ `confirmed=true` (người dùng đã đồng ý rõ ràng ở turn trước đó). |


## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  * Các sửa đổi liên quan đến việc từ chối các yêu cầu ngoài scope (như toán học, code Python).
  * Quy tắc chỉ hỏi xác nhận đối với các thao tác ghi dữ liệu (Telegram, tạo file sổ tay) và không hỏi đối với thao tác đọc dữ liệu.
  * Các quy tắc mapping trực tiếp tên người nổi tiếng thành screenname/handle cụ thể.
  * Việc ép buộc model phải luôn truyền tham số rõ ràng khi gọi tool clarify.

- **Which fixes belonged in `tools.yaml`?**
  * Mô tả các tham số của tool rõ ràng, thiết lập các kiểu Enum cụ thể để model lựa chọn chuẩn (ví dụ các trường `response_type` trong clarify, `timeframe`, `topic` trong lookup).
  * Mô tả chi tiết trong description của tool để phân định rõ ranh giới khi nào nên dùng tool này, khi nào dùng tool khác (như `scholar` so với `papers`).

- **Which failure needed manual review instead of automatic grading?**
  * Lỗi thực thi logic bên trong tool (ví dụ do lỗi mạng khi fetch URL, hoặc thiếu API Key trong file `.env` dẫn đến crash nhưng tool vẫn được model gọi đúng). Những ca này tự động chấm vẫn báo PASS vì model đã chọn đúng tool và đối số, nhưng kết quả thực tế trả về cho người dùng bị rỗng/lỗi, cần review thủ công.

- **What would you improve next?**
  * Tích hợp thêm các thư viện xử lý thông tin chuyên sâu như đọc và phân tích file PDF học thuật hiệu quả hơn.
  * Tối ưu hóa giao diện Streamlit để hỗ trợ live-stream các phản hồi của Agent và hiển thị các bước gọi tool theo thời gian thực (real-time trace visualization).

