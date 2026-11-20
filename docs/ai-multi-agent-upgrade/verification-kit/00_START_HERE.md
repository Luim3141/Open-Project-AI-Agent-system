# QLDAPM — BỘ KIỂM TOÁN ĐỘC LẬP + SỬA LỖI THÍCH ỨNG (Quick Tunnel được phép)

**Phiên bản audit:** 2026-10-17 / `CR-KEEP-QUICK-TUNNEL`  
**Nguồn kiểm tra:** Gemini `FINAL_REPORT_HANDOVER.md` và `RELEASE_NOTES_LOCAL_V2.md` (chỉ là tuyên bố, chưa là chứng cứ độc lập).  
**Dự án:** `D:\AI project\QLDAPM chat` / `docs\ai-multi-agent-upgrade`.

## Những yêu cầu chính
- Windows máy chủ local + Docker/WSL2; tối đa **20 users**; Gemini API **Free Tier**, không VPS, không paid feature, không GitHub Research workflow.
- **Cloudflare Quick Tunnel được giữ nguyên theo yêu cầu chủ dự án**, dùng để truy cập có xác thực từ ngoài LAN; không thay bằng LAN-only, không tự ý gỡ/disable tunnel.
- Bảo toàn OpenProject, Rails/RBAC `PM-only-write`, n8n Community, Gateway, Agent Runtime/Supervisor, Second Brain, Control Center.
- Sau khi mở Docker Desktop, container tự phục hồi nếu engine, restart policy và phụ thuộc cho phép; Quick Tunnel URL không được giả định cố định. Bất cứ gì chưa đo/kiểm đều là `UNVERIFIED`.

## Sử dụng
1. Giải nén ZIP vào `D:\AI project\QLDAPM chat\docs\ai-multi-agent-upgrade\` để có đường dẫn cuối `docs\ai-multi-agent-upgrade\verification-kit\01_GEMINI_MASTER_PROMPT.md`. ZIP đã chứa sẵn thư mục gốc `verification-kit`; không tạo thêm tầng thứ hai.
2. Dừng mọi coding agent khác đang ghi cùng working tree; bật Docker Desktop, đợi Docker Engine ready.
3. Mở **Antigravity** trên workspace GỐC `D:\AI project\QLDAPM chat`.
4. Dán nội dung **`01_GEMINI_MASTER_PROMPT.md`**. Bắt đầu Wave 0 **đọc/chẩn đoán**, chưa mutation.
5. Agent phải thực hiện checklists `02`–`09` và lưu `verification_runs/<timestamp>/...` trong kế hoạch dự án.
6. Yêu cầu bằng chứng thật, lỗi có reproduction/test, báo cáo cuối có trạng thái `PASS/PASS_WITH_LIMITATIONS/FAIL/BLOCKED`.
7. Gửi lại cho ChatGPT audit report, test results và handoff; không chỉ gửi văn bản kể đã xong.

## Bộ file
- `01_GEMINI_MASTER_PROMPT.md`: Prompt chính cho Gemini/Antigravity.
- `02_TEST_MATRIX.md`: Matrix test ID, cấp độ, pass/evidence.
- `03_WINDOWS_RUNBOOK.md`: Lệnh Windows/Docker/PowerShell.
- `04_GITHUB_SKILLS_AND_TOOLS.md`: Skills có nguồn GitHub và cách kiểm tra/cài an toàn.
- `05_ADAPTIVE_DEBUG_PLAYBOOK.md`: Chẩn đoán theo triệu chứng/root cause, cách viết fix.
- `06_FREE_SECURITY_RELEASE_POLICY.md`: Bất biến chi phí, quyền, network, dữ liệu và Quick Tunnel.
- `07_TEST_CODE_EXAMPLES.md`: Ví dụ code kiểm thử; PHẢI chỉnh theo API thật trước chạy.
- `08_RELEASE_GATES_AND_HANDOFF.md`: Quy trình nghiệm thu lại 113 task và bàn giao.
- `09_QUICK_TUNNEL_TESTS.md`: Kịch bản remote truy cập và bảo mật tunnel.
- `scripts/audit_claims.py`: Kiểm tra read-only những claims/artifacts có thể kiểm tra từ cây thư mục.
- `source_reports/`: Hai báo cáo gốc để đối chiếu, không phải bằng chứng.

## Cảnh báo
**Chưa có quyền đọc source/runtime Windows của cậu trong lượt này.** Hai báo cáo không đủ chứng minh 100% PASS, 20 người thực, zero billing hay no-touch startup. Auditor phải tách `CLAIMED` và `VERIFIED`. Không chạy destructive tests trên main. Không công khai API key/log chứa token. Không tắt Quick Tunnel vốn được owner yêu cầu.
