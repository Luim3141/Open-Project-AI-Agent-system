# Các giới hạn nghiệm thu còn lại — Main, 27/10/2026

Approval Gemini `a10e19d6e02df9928ebeb8307cd45f200187efadf81aad328bde9bc31d75d58f` đã được dùng đúng một lần. Run `f04b5c59-26dc-40af-b999-00298b298ca0` hoàn tất; không cần duyệt lại hoặc regenerate. Xem `CODEX_WF10_FRESH_MODEL_RECEIPT_READBACK.json`.

| Hạng mục | Trạng thái và điều kiện thực tế |
|---|---|
| Native mutation mới trên Main | Chưa được cho phép. Cần proposal/hash/version cụ thể và quyết định human mới khi có thao tác hợp lệ; approval Gemini không cấp quyền này. Các approval cũ đã consumed. |
| Full application QA/fix/retest/closure | PARTIAL kỹ thuật: đã deploy source/scope/analysis; producer cho application fix/build và Native Subtask bốn trạng thái chưa hoàn thiện. #371 chưa có defect/application source mapping; không gán test không liên quan để đóng task. Đây còn là việc phát triển, không phải thiếu approval Gemini. |
| Browser UAT mới | BLOCKED bởi browser URL policy đã ghi nhận. Không đổi browser/CDP/Playwright để vượt chặn. Board API và ActionView fixture không chứng minh thao tác kéo thả hoặc phiên đăng nhập UI mới. |
| Full Qdrant restore | BLOCKED_RESTORE_POLICY. Không retry bằng đường khác. Các restore PG/SQLite/n8n/assets và fault tests riêng không phải atomic cross-service DR. |
| Hai historical comment outcomes | UNKNOWN_HOLD. Không tìm được own authoritative receipt hoặc exact marker/text; thiếu dữ liệu không chứng minh write thất bại. Không replay hay tự sửa lịch sử. |
| Ba legacy Qdrant points | Ownership/producer chưa chứng minh; payload nguyên vẹn, không đăng ký SQLite, tiếp tục loại khỏi retrieval. Không delete hoặc hợp thức hóa từ namespace/project claim. |
| External notifications | BLOCKED_CONFIGURATION: chưa có recipient/channel do user chỉ định. Adapter/local delivery được test; không tạo người nhận hoặc gửi thử ra ngoài. |
| Mutable model/provider/Agent editors | NOT_IMPLEMENTED ngoài các cấu hình được contract hiện tại hỗ trợ; không tạo dashboard giả hoặc đổi quota/provider. |

Nguồn trạng thái runtime: `CODEX_MAIN_CONTINUATION_CHECKPOINT.json`. Full release vẫn PARTIAL; không suy ra GO từ healthy, active workflows hoặc số tests PASS.
