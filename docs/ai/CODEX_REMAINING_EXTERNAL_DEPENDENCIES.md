# Các điều kiện còn thiếu — Main

Trạng thái toàn dự án vẫn **PARTIAL**, không phải FULL GO. Đọc `CODEX_MAIN_CONTINUATION_CHECKPOINT.json`; image trong báo cáo cũ chỉ là lịch sử.

| Điều kiện | Trạng thái và phạm vi |
|---|---|
| Quyết định QA thật trên Main | Evidence `d4d5aa97-a716-550d-88e9-de04b9caf9c9` vẫn `pending_qa`. QA23 review bằng chính danh tính của mình, sau đó PM19 review độc lập. Owner18 là requester nên không được tự review. Không tạo quyết định thay người. |
| Native mutation tiếp theo | Cần proposal/hash/approval hợp lệ mới và đủ business prerequisites. Các approval Scenario F/tree/schedule cũ đã dùng hết. Không replay hoặc dùng #370 làm resource cho mutation mới. |
| External notifications | `BLOCKED_CONFIGURATION`: chưa có recipient/channel do người dùng chỉ định. Local metadata delivery đã có; chưa gửi thử ra ngoài. |
| Full Qdrant restore | `BLOCKED_RESTORE_POLICY`: automatic tool review trước đó đã chặn. Không dùng công cụ, target hoặc cách gọi khác để vượt chặn. Các bài recovery độc lập khác vẫn tiếp tục. |
| Hai comment outcome lịch sử | `UNKNOWN_HOLD`: chưa có Native receipt chứng minh đã ghi hoặc không ghi. Không replay, xóa hay sửa lịch sử. Xem `CODEX_WF14_FINAL_RECOVERY_RESULT.json`. |
| Ba legacy Qdrant points | Producer ownership `NOT_PROVEN`; giữ nguyên và loại khỏi retrieval bằng policy SQLite. Không tự xóa. |
| Browser automation | Policy đã chặn. Giữ human UAT đã xác nhận; không chuyển browser/CDP/Playwright để vượt chặn. API/controller/ActionView tests không phải visual browser PASS. |

Những việc kỹ thuật còn làm độc lập được không phải dependency bên ngoài: versioned Native relation/scheduling; producer delete/tombstone có provenance; qualification retest/release/Subtask completion và full Bug lifecycle trên clone; kiểm chứng thêm vận hành và backup. Supervisor local đã đọc được verified QA artifact trên Main; việc này không thay human QA/approval hoặc giải quyết các gaps còn lại. Không chuyển workflow thành PASS chỉ vì service healthy.

Native delete bị Core guard chặn khi thiếu local approval contract. Không bật thread flag bằng tay, tắt guard hoặc suy ra physical deletion từ 404/visibility withdrawal để hoàn thành test.
