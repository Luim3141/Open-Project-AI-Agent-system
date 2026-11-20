# MỤC LỤC BẰNG CHỨNG ẢNH CHỤP PLAYWRIGHT E2E (PLAYWRIGHT TRACE INDEX)
## DỰ ÁN: QLDAPM MAIN — PHASE 3.1 BROWSER UAT TRACES

---

### 1. Danh mục ảnh chụp màn hình thực tế (Evidence Screenshots)

Toàn bộ ảnh chụp được lưu trữ tại thư mục: `docs/ai/engineering/PHASE31_RECOVERY/screenshots/`.

| Tệp tin | Kích thước | Thời gian tạo | Mô tả & Nội dung chứng minh pháp y |
|---|---|---|---|
| [`01_command_center_loaded.png`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE31_RECOVERY/screenshots/01_command_center_loaded.png) | 224,814 bytes | 2026-10-31 12:15:32 | **Giao diện Command Center tải thành công (HTTP 200):** Chứng minh User 18 (AI System Owner) được xác thực thành công, toàn bộ sidebar, thanh KPI, bảng điều khiển và danh sách nhiệm vụ hiển thị hoàn chỉnh, không có lỗi 403. |
| [`02_agent_workforce.png`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE31_RECOVERY/screenshots/02_agent_workforce.png) | 170,961 bytes | 2026-10-31 12:15:36 | **Minh bạch hóa Đội ngũ Agent:** Tab "Đội ngũ Agent" hiển thị đầy đủ và trung thực: Reviewer vận hành theo `Local-Policy Exact-Diff (0 LLM Calls)`, QA vận hành theo `Pytest Runner (0 LLM Reasoning)`, Dev vận hành qua `OpenClaw Tool Execution`, PM/BA dùng `gemini-3.5-flash-lite`. |
| [`03_sync_github_result.png`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE31_RECOVERY/screenshots/03_sync_github_result.png) | 225,215 bytes | 2026-10-31 12:16:03 | **Kết quả Đối soát GitHub (HTTP 200):** Nút "Sync GitHub" được nhấn thành công, đối soát 5 Stacked PRs mà không gặp lỗi 409 Conflict. Nút bấm tự động phục hồi (0 submitting buttons), toast thông báo đối soát thành công xuất hiện. |
| [`04_snapshot_result.png`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE31_RECOVERY/screenshots/04_snapshot_result.png) | 224,924 bytes | 2026-10-31 12:16:19 | **Kết quả Tạo Snapshot Tức thời (HTTP 200):** Nút "Snapshot Tức Thời" phản hồi HTTP 200, tạo bản báo cáo markdown mới trong SQLite và hiển thị thông báo thành công cho người dùng, nút bấm mở khóa hoàn toàn. |
| [`05_run_once_result.png`](file:///D:/AI%20project/QLDAPM%20chat/docs/ai/engineering/PHASE31_RECOVERY/screenshots/05_run_once_result.png) | 224,841 bytes | 2026-10-31 12:16:33 | **Kết quả Chạy Đơn vị Kiểm soát (RUN ONCE - HTTP 200):** Nút "RUN ONCE" gửi yêu cầu thành công, tự động tra cứu đúng unit trong backlog, không bị treo spinner (0 submitting buttons), hiển thị thông điệp tiếp nhận / bàn giao rõ ràng. |

---

### 2. Phương pháp kiểm thử và tái tạo (Reproduction Steps)
Để tái chạy bộ kiểm thử Playwright tự động và kiểm chứng toàn bộ các ảnh chụp trên:
```bash
node "C:\Users\LUIM\.gemini\config\skills\playwright-skill\run.js" "D:\AI project\QLDAPM chat\tools\verify_phase31_real_e2e.js"
```
Kết quả JSON lưu tại: `docs/ai/engineering/PHASE31_RECOVERY/FUNCTIONAL_TEST_RESULTS.json`.
