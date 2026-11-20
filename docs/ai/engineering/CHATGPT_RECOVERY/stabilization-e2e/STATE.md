# Fresh E2E stabilization — verified path, với giới hạn

- Marker `QLDAPM-E2E-20261102-STABILIZATION-001`; intake qua Gateway HTTP, actor PM 20, Project 6, parent #379.
- Planning run `4e3626a4-7af2-47ff-b1e7-c2bf38f602f1` succeeded; PM/BA model thật, plan PUBLISHED, tạo một WP #389 và unit `feedback-e44b47e2e8610c4f`, base PR #7.
- Development run `814f7a28-6c1a-4d2e-82d6-f0d118e2081c` succeeded không cần resume: Dev, reviewer PASS trên diff `d7a2bf7c84aaeaf41663e9e6e9e8c75d8712dacaf2edce4d2e2f87c796f20497`, QA PASS, acceptance **29 passed**. `timeline.jsonl` ghi trạng thái/ACK thực tế.
- Backup trước mutation: private operator `stabilization-e2e-prechange-20261102`. Marker không trùng, queue ban đầu OFF/idle, provider Free và billing disabled theo policy; local/remote branch mới chưa có lúc preflight.
- GitHub REST đọc lại [PR #8](https://github.com/Luim3141/mini-task-manager/pull/8) OPEN, head `b20fb554cb0b45f2938ac11ba9e736708dcb1bf0`, base nhánh PR #7; không merge. Native #389 version 2 ghi PR #8. GitHub Sync lần đầu cập nhật một activity, lần hai zero changes (`github-sync-1.json`, `github-sync-2.json`).
- Gateway outbox 13 ACK và 13 observation tương ứng, trace/correlation và n8n execution IDs trong `n8n-observations.json`. WF04 hiện không lưu success/error execution history; ACK không chứng minh history UI đã lưu.
- Knowledge read-back ngay trong run và truy vấn riêng trả `/work_packages/389`, version 2, dense READY (`rag-readback.json`). Đây là query scope ID, không chứng minh benchmark semantic VN/EN tổng quát.
- Report ON_DEMAND `b69ee21a-86d9-4d9d-bd8d-fdd12245db6f` được tạo/đọc lại HTTP 200, có WP #389 và PR #8 (`report.json`, `report-readback.json`). Báo cáo AI có narrative thật được test riêng trước run, không gộp làm bằng chứng cho report này.
- Sau run: queue finished, mode OFF, active 0, không có Native request outcome chưa rõ của run. Project 5: 341 dòng bảng work_packages khớp toàn bộ cột với snapshot trước E2E trước đó. Không chứng nhận dữ liệu mọi bảng hoặc Owner manual UAT.

Các mắt xích API của bài test này có read-back thật. Semantic RAG tổng quát, WF04 retention, master-key migration, 16 business workflow và Owner UI UAT vẫn OPEN/BLOCKED; không coi bài test này là FULL SYSTEM PASS.
