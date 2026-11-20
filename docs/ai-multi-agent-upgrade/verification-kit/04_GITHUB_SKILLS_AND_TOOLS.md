# 04 — GITHUB SKILLS & QA TOOLS (NGHIÊN CỨU NGÀY 17/10/2026)

**Lưu ý:** Skills là hướng dẫn trong file `SKILL.md`; kiểm thử browser/load/security bằng tool riêng. Không nhầm 2 loại. Nghiên cứu GitHub ở đây nhằm cải thiện kỹ năng coding/QA **không phải triển khai GitHub Research workflow cho sản phẩm QLDAPM**.

## A. Chính thức: Google Antigravity
Tài liệu: https://www.antigravity.google/docs/skills?tab=ide

- Workspace skills: `.agents/skills/<name>/SKILL.md` (legacy `.agent/skills` có thể tương thích nhưng không ưu tiên).
- Global skills trong IDE/App: `~/.gemini/config/skills/<name>/SKILL.md`.
- Trong Antigravity, xem Customizations menu để kiểm tra skills được load; hoặc dùng `/<skill-name>` khi phù hợp.
- `SKILL.md` có YAML frontmatter `name` và `description`. Đừng cài global nếu kỹ năng chỉ cho QLDAPM.

## B. Ưu tiên skills từ repo có nguồn rõ ràng
| Nguồn GitHub | Skill | Tác dụng trong audit | Quyết định |
|---|---|---|---|
| https://github.com/obra/superpowers | `systematic-debugging` | Tìm root cause trước khi sửa | Ưu tiên nếu chưa có |
| https://github.com/obra/superpowers | `verification-before-completion` | Không tuyên bố PASS khi chưa chạy test | Ưu tiên nếu chưa có |
| https://github.com/obra/superpowers | `test-driven-development` | RED → GREEN → REFACTOR cho bug fix | Ưu tiên nếu chưa có |
| https://github.com/obra/superpowers | `requesting-code-review` | Review độc lập diff & acceptance | Có thể thêm |
| https://github.com/anthropics/skills | tiêu chuẩn/ví dụ `SKILL.md` | Tham khảo chuẩn tạo skill QA nội bộ | Tham khảo, không bắt cài hàng loạt |

**Repo và tài liệu tương ứng:**
- https://github.com/obra/superpowers/tree/main/skills/systematic-debugging
- https://github.com/obra/superpowers/tree/main/skills/verification-before-completion
- https://github.com/obra/superpowers/tree/main/skills/test-driven-development
- https://github.com/obra/superpowers/tree/main/skills/requesting-code-review
- https://github.com/anthropics/skills

## C. Quy trình kiểm tra/cài an toàn cho Antigravity
1. Kiểm tra `.agents/skills`, global skills, `AGENTS.md`, `GEMINI.md` và skill tên tương tự đã có; không ghi đè.
2. Với skill còn thiếu: review owner/repo/commit SHA, license, toàn bộ `SKILL.md` + scripts/hooks phụ thuộc; chỉ tải từ upstream chính thức HTTPS.
3. Clone vào TEMP nằm ngoài repo; không chạy script tải về tự động; không chạy remote code chưa đọc. Ưu tiên copy **riêng** thư mục skill đã kiểm tra.
4. Copy vào `.agents/skills/<name>/SKILL.md`, giữ file kèm theo có liên quan, kiểm tra frontmatter; không sửa behavior rules khác.
5. Kiểm tra skill xuất hiện trong Customizations/slash invocation. Ghi `SKILL_INSTALL_LOG.md` gồm SHA nguồn, license, file và test sử dụng. Nếu công cụ không hỗ trợ import skill, tự tạo skill QLDAPM riêng tổng hợp nguyên tắc, không giả vờ skill được cài.
6. Không cài plugins có quyền remote shell/host/admin hoặc request secret chỉ để audit. Không copy `AGENTS.md` từ repo lạ ghi đè của dự án.

**PowerShell minh họa (chỉ chạy sau khi review source):**
```powershell
$root = 'D:\AI project\QLDAPM chat'
$tmp = Join-Path $env:TEMP 'ql-superpowers-reviewed'
# Chọn temp path mới chưa chứa dữ liệu quan trọng. Không tự xoá temp có sẵn.
git clone --depth 1 https://github.com/obra/superpowers.git $tmp
git -C $tmp rev-parse HEAD
Get-Content (Join-Path $tmp 'skills\systematic-debugging\SKILL.md') -TotalCount 80
# Kiểm tra toàn bộ nội dung/scripts/licensing trước lệnh Copy-Item.
$dest = Join-Path $root '.agents\skills\systematic-debugging'
if (-not (Test-Path $dest)) {
  New-Item -ItemType Directory -Path $dest -Force | Out-Null
  Copy-Item (Join-Path $tmp 'skills\systematic-debugging\*') $dest -Recurse
} else { Write-Host 'EXISTING — review only, do not overwrite' }
```
Không `curl | bash`, `iwr | iex`, `npx` không pin/không kiểm tra behavior theo kiểu mù. Nếu npx skills CLI đã cài và được xác minh, có thể dùng `npx skills add ...` cho từng skill sau khi xem `--help` và lock nguồn; không bắt buộc.

## D. Tools QA open-source (không phải skill)
| Repo | Chức năng | Phạm vi |
|---|---|---|
| https://github.com/microsoft/playwright | Browser E2E, API, session isolation | Test role/cookie/Quick Tunnel |
| https://github.com/microsoft/playwright-mcp | Browser tool cho coding agent | Tùy chọn, không thay E2E assertions |
| https://github.com/grafana/k6 | Load 1→5→10→20 virtual users | Chỉ staging/LAN, không stress public tunnel |
| https://github.com/aquasecurity/trivy | Scan source/image CVE/config/secrets | Read-only, không cần Socket mount tùy tiện |
| https://github.com/zaproxy/zaproxy | Baseline passive vulnerability scanning | Chỉ môi trường owned/staging, low rate |

Nếu Node/Playwright chưa có, agent được phép đề xuất/cài dev tools miễn phí sau khi kiểm tra quyền, disk space và ảnh hưởng repo. Cài trong isolated QA harness, không lẫn production dependencies. Trivy scanner có thể cần tải cơ sở dữ liệu CVE từ Internet; không gửi source private lên cloud scanning service. Nếu thiếu mạng/bị chặn, đánh dấu TOOL_UNAVAILABLE, làm manual tests tương đương và không bịa PASS.

## E. Kết quả cần lưu
`SKILL_INVENTORY.md`: active skills thực tế, nguồn. `SKILL_INSTALL_LOG.md`: chỉ những gì cài thật, SHA và trạng thái. `TOOL_VERSIONS.md`: Playwright, k6, Trivy, ZAP và license/chi phí, không cài thừa.
