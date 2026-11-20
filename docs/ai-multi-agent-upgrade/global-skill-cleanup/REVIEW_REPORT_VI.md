# ĐÁNH GIÁ ĐỘC LẬP GLOBAL SKILLS — 17/10/2026

**Nguồn đầu vào**: SKILLS_INVENTORY.json (1.562 bản ghi), SKILLS_FULLTEXT.zip (1.562 `SKILL.md`), SKILLS_DUPLICATES.csv, SKILLS_SOURCE_MAP.csv, SKILLS_AUDIT_OVERVIEW.md, MANIFEST.json. Đã kiểm tra tất cả entry ZIP và so khớp hash.

## Kết quả và quyết định

| Chỉ số | Giá trị |
|---|---:|
| Global user-installed (chỉ mục tiêu thay đổi) | 1.463 |
| Global KEEP được chọn | 77 |
| Global DELETE_AFTER_CHECK | 1386 |
| Plugin skills không chạm tới | 91 |
| Built-in skills không chạm tới | 8 |
| Estimated global prompt tokens trước | 88.382 |
| Estimated global prompt tokens sau | 5,071 |
| Tổng **other-customization** gồm global+plugin+built-in, ước tính sau | 18,262 |
| SHA-256 mismatch giữa fulltext ZIP và inventory | 50 (toàn bộ là global) |
| Exact duplicate full SKILL.md theo inventory | 0 nhóm |

Mốc ngân sách 20.000 tokens có thể đạt cho nhóm Other theo phép cộng ước tính trên, nhưng **không bảo đảm**: UI sử dụng tokenizer/cơ chế tính riêng, quyền Rules (~9.605 tokens) có thể hiển thị ngân sách riêng, và plugin có thể thay đổi. Cần kiểm tra UI sau khi mở lại Antigravity.

## Quy tắc phân loại

- **KEEP**: 77 global skill phục vụ đa dự án, tập trung phương pháp phát triển, test, ngôn ngữ/phần mềm phổ biến, AI/MCP, Docker, API, PostgreSQL, tài liệu, giao diện. Giữ một đại diện theo khả năng thay vì hàng chục persona tương tự.
- **DELETE_AFTER_CHECK**: 1.386 global skill còn lại, do trùng chức năng, quá chuyên biệt, ít cần làm mặc định hoặc bị dư thừa bởi built-in/plugin. Đây là **đề xuất tinh gọn global**; không phải tuyên bố mọi skill bị đề xuất xóa đều chất lượng kém.
- Các trường `closest_kept`/`similarity_proxy` là **độ gần TF-IDF của tên và mô tả**, chỉ mang tính hỗ trợ; không phải đánh giá công bằng AI, không chứng minh trùng nội dung/hành vi hoàn toàn.
- Không giữ/xóa dựa **duy nhất vào số sao GitHub**.

## Những nhóm bị loại nhiều

- Azure SDK: ~124 thư mục, hướng dẫn rất chuyên biệt trong khi global cần dùng cho nhiều loại dự án.
- SEO/Marketing: ~68 theo bộ phân loại tên; có thêm nhiều marketing automations ở nhóm khác.
- App automation: ~92 thư mục cho dịch vụ ít sử dụng mặc định.
- Cloud/Kubernetes: ~22 thư mục theo tiền tố và hàng loạt biến thể chuyên biệt khác.
- Agent/code-review/TDD: chỉ giữ các workflow khác biệt đủ rõ; tránh giữ nhiều persona thay nhau trả lời cùng một vấn đề.
- 1.000 mục 'Other/niche/overlap': được loại theo **chính sách whitelist global 77 skill** chứ không thể khẳng định cùng chức năng hay vô giá trị. Cài lại theo project khi cần.

## GitHub — đo mức phổ biến đúng cách

**Không đồng nhất source giả định với bản đã cài.** Phần lớn skill global không có URL nguồn được xác minh (trong manifest: 1/1.463). Các link sau là repo tham chiếu, không tự động xác nhận file trên máy là bản nguyên gốc:

| Repo cộng đồng/chính thức | Tham khảo popularity (snapshot tìm kiếm 10/2026) | Tác dụng | Mức tin cậy cho skill đang cài |
|---|---|---|---|
| https://github.com/anthropics/skills | ~181.000 stars | Chuẩn cấu trúc skill, skills tài liệu | Chỉ uy tín repo, không chứng minh các skill local là upstream |
| https://github.com/obra/superpowers | ~291.000 stars | Systematic debugging, TDD, plan/review | Local systematic-debugging giống framework, chưa xác minh SHA tương đương upstream |
| https://github.com/vercel-labs/agent-skills | ~31.000 stars | React best practices, web guidelines | Local skill tham chiếu nội dung Vercel, nhưng file snapshot không xác minh commit |
| https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | ~134.000 stars | Thiết kế/UI/UX | Trùng tên/chức năng; không xác nhận local bundle khớp bản phát hành |
| https://github.com/microsoft/playwright-mcp | ~38.000 stars | Browser automation qua MCP | **Không đồng nhất** repo MCP với global `playwright-skill` |
| https://github.com/microsoft/skills | 175 skill được công bố trong repo | Azure SDK/Foundry | Uy tín nhà phát triển không có nghĩa 124+ Azure skills nên tải global khi không dùng Azure |
| https://github.com/olgasafonova/SkillCheck-Free | ~41 stars | Kiểm tra cấu trúc Agent Skills | Không phổ biến bằng các repo lớn; vẫn hữu ích vì có kiểm tra cụ thể |
| https://github.com/aptratcn/skill-audit | Không có số sao đã xác minh | Audit skill trước khi cài | Rà soát nội dung trước khi chạy; repo tự mô tả phương pháp quét |

**Ý kiến cộng đồng (không phải khảo sát đại diện):**
- https://www.reddit.com/r/ClaudeCode/comments/1vvgsia/is_superpowers_still_relevant/ — người dùng khen khâu brainstorming/TDD; một số cho rằng nhiều skill ảnh hưởng đến phán đoán và tăng token.
- https://www.reddit.com/r/ClaudeCode/comments/1rmi6pr/anyone_else_not_a_fan_of_the_superpowers_plugin/ — phản ánh workflow cứng nhắc, quá nhiều bước.
- https://www.reddit.com/r/ClaudeAI/comments/1uhed8x/why_are_all_the_claude_code_skill_files_i_see/ — phê bình loại skill chỉ nói 'you are expert' mà thiếu hành động cụ thể.
- https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues — có issue về cấu hình, tính tương thích và quyền MCP; cần xem trước khi chạy scripts.

Đây là dữ liệu cộng đồng ở **cấp bộ skill/repository**, không phải hàng nghìn review độc lập cho từng skill. Không đủ provenance để gán star hoặc điểm cộng đồng cho 1.463 mục.

## CẢNH BÁO: ZIP và inventory không nhất quán ở 50 SKILL.md

So sánh SHA-256 từng SKILL.md trong ZIP với trường `skill_md_sha256` của inventory thấy **50 trường hợp không khớp**; 50/50 thuộc global. Một khả năng là xuất bản đã được ẩn/sửa nội dung nhạy cảm, nhưng chưa có bằng chứng giải thích chính thức. Xem `HASH_RECONCILIATION.csv`.

Do đó **KHÔNG dùng fulltext ZIP làm giá trị hash chuẩn để xóa**. Manifest giữ SHA-256 từ inventory. Gemini phải kiểm tra SKILL.md thật trên máy của cậu khớp với manifest, xác nhận đúng thư mục con trực tiếp của `~/.gemini/config/skills`, kiểm tra symlink/junction và các tham chiếu chéo; nếu khác thì SKIP để rà lại. Không xuất raw secret.

## Lưu ý bảo mật ngoài phạm vi xóa

`SKILLS_AUDIT_OVERVIEW.md` ghi nhận global terminal grants trong `~/.gemini/config/config.json`, có lệnh tải PowerShell và pipe vào `iex`. Dọn skill **không xóa được quyền thực thi đó**. Nên audit `config.json` riêng, thu hồi grant nguy hiểm nếu không cần, sau khi chủ dự án cho phép. Không thực thi bất kỳ mã nào chỉ vì xuất hiện trong nội dung SKILL.md.

## Thứ tự áp dụng

1. Dừng Antigravity/Codex/agent khác ghi file; không chạy song song task source QLDAPM.
2. Copy bộ này vào máy; xác minh checksum file manifest và khớp danh sách thực tế.
3. Dry-run toàn bộ 1.386 ứng viên, in rõ các mục SKIP (hash khác, symlink, thiếu file, đang được tham chiếu, folder lạ, plugin/builtin).
4. Backup nén có kiểm tra SHA, đặt **ngoài các thư mục Antigravity scan**.
5. Xóa vĩnh viễn các thư mục global khớp chính xác trong danh sách đã duyệt; giữ 77 thư mục KEEP.
6. Khởi động lại Antigravity; kiểm tra skill count, token budget, skills quan trọng và chức năng QLDAPM.
7. Nếu phát sinh lỗi, khôi phục các skill cần thiết từ backup theo manifest, không restore tràn lan.

**Sự khác biệt bản fulltext và manifest, cùng trạng thái plugin chưa xác minh hoàn toàn, có thể khiến số lượng thực xóa nhỏ hơn 1.386. Báo cáo phải công khai SKIPPED, không ép kết quả.**
