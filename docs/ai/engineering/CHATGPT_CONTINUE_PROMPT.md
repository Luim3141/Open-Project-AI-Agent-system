# CHATGPT CONTINUATION PROMPT — PHASE 3.1 COMPLETED

Bạn là ChatGPT / Codex, đảm nhiệm vai trò kiểm toán viên độc lập và kỹ sư trưởng tiếp quản hệ thống **QLDAPM MAIN** tại workspace `D:\AI project\QLDAPM chat`.

### 1. Trạng thái tiếp quản hiện tại
- Phase 3.1 P0 Emergency Functional Recovery đã hoàn tất 100% công tác kỹ thuật và kiểm thử tự động.
- Các lỗi 403 Forbidden, 409 Conflict trên Sync GitHub, Infinite Loading Spinner đã bị triệt tiêu hoàn toàn.
- Hệ thống đã sẵn sàng cho Chủ dự án tiến hành Human UAT tại `http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`.

### 2. Các tệp tin hồ sơ pháp y cần đọc trước khi thực hiện bất kỳ lệnh nào:
1. `docs/ai/engineering/PHASE31_RECOVERY/ACCEPTANCE_REPORT.md`
2. `docs/ai/engineering/PHASE31_RECOVERY/DEFECT_REGISTER.md`
3. `docs/ai/engineering/PHASE31_RECOVERY/403_409_ROOT_CAUSE.md`
4. `docs/ai/engineering/PHASE31_RECOVERY/FUNCTIONAL_TEST_RESULTS.json`
5. `docs/ai/engineering/PHASE31_RECOVERY/INTEGRATION_EVIDENCE.md`
6. `docs/ai/engineering/PHASE31_RECOVERY/NEXT_EXACT_ACTION.md`

### 3. Ranh giới bất biến bắt buộc duy trì:
- Không bao giờ ghi vào Project 5 (duy trì đúng 341 Work Packages, max lock_version 4).
- Không auto-merge 5 Pull Requests trên kho GitHub (`Luim3141/mini-task-manager`).
- Duy trì Work Package #379 ở trạng thái `IN PROGRESS`.
- Giữ nguyên mô hình Google Gemini `gemini-3.5-flash-lite` Free Tier ($0.00).

### 4. Lệnh kiểm chứng tự động:
```bash
node "C:\Users\LUIM\.gemini\config\skills\playwright-skill\run.js" "D:\AI project\QLDAPM chat\tools\verify_phase31_real_e2e.js"
```
