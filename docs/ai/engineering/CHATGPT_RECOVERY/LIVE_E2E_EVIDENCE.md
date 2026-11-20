# Live E2E — post-30218aff

Fresh stabilization E2E sau patch là WP #389 / PR #8; evidence và timeline đầy đủ tại `stabilization-e2e/STATE.md`. Nội dung bên dưới mô tả run #387 trước đó.

Trạng thái: **RUN SUCCEEDED; CÁC BƯỚC CHÍNH CÓ READ-BACK**. Semantic RAG tổng quát và Owner manual UAT vẫn chưa đạt/không thuộc phép test này.

- Project 6, Gateway HTTP intake marker `QLDAPM-E2E-20261101-POST-ROLLOUT-001`, planning run `3376cdf8-94e0-4587-b656-dfadc61d4071`: PM và BA dùng Gemini thật; plan PUBLISHED và tạo Native WP #387 dưới #379. Xem `post30218-20261101T1540Z/plan-readback.json`.
- Development run `f136866a-b7e4-4ad8-bbd7-d846343163d0` đã thực sự chạy OpenClaw Dev trong worktree riêng. Lần đầu bị giới hạn 12 provider calls, trả `OPENCLAW_STEP_NOT_COMPLETED`; diff còn nguyên. Phép test độc lập trên diff: 26 passed; đây không phải verdict của QA agent.
- Resume đầu bị `ENGINEERING_DELIVERY_FAILED` tại prepare, chưa xác định được nguyên nhân. Phép tái hiện `prepare` độc lập sau đó PASS; resume thứ hai cùng run/checkpoint đã vào DEVELOPING. Không tạo thêm WP.
- Gateway lifecycle outbox đã ACK và nhận observation từ WF04 trước và sau rollout n8n. WF04 hiện không giữ execution data success/error; không nhầm trace metadata với execution history có thể xem trong n8n.
- Reviewer OpenClaw PASS trên diff hash `04fc6371df90be5aa161a81607e2b8081259e3e7bf0e4bdc14c9f1cc75bf8ad4`; QA OpenClaw PASS với exit 0 và acceptance host 26 passed. Worker commit/push `a150f3d690288ff95451c2667954f09661aa9604`, PR [#7](https://github.com/Luim3141/mini-task-manager/pull/7) OPEN, base nhánh PR #6. Không merge.
- Native read-back: child #387 version 2, parent #379 version 4, PR #7. Worker báo knowledge retrieval count 1 nhưng citation trong run là `/work_packages/379`. Truy vấn Gateway riêng có `native_ids=[387]` trả `/work_packages/387`, version 2 và dense state READY; evidence `post30218-20261101T1540Z/rag-wp387.json`. Phép lọc định danh này không chứng minh semantic retrieval tổng quát. Run kết thúc `succeeded`, 17 lifecycle events ACK.
- ON_DEMAND report `98237e37-b61b-403d-b8da-f2fe86179c6b` được tạo và đọc lại qua Gateway HTTP 200; evidence `report-generate.json`, `report-readback.json` cùng thư mục. Owner manual UAT chưa thực hiện.

Sau run, Gateway được cập nhật để không chấp nhận citation parent làm bằng chứng child; query #387 riêng vẫn trả đúng ID/version/citation sau deployment (`rag-wp387-postdeploy.json`). Chưa chạy business E2E mới sau patch này.

Raw artifacts: `post30218-20261101T1540Z/` và `../runs/f136866a-b7e4-4ad8-bbd7-d846343163d0/`. Không lặp lại Native operation nếu journal có outcome chưa rõ.

## Phase 2 final — WP #390 / PR #9

Một fresh task được Owner cho phép đã dùng hết: marker `QLDAPM-E2E-20261102-PHASE2-FINAL-001`. Planning `8751d17a-4c6c-4f5f-b00c-6e1239f5353c` → WP #390 / unit `feedback-9d0ff35386a63183`; development `447d4fd9-fd03-4a41-9468-09bad8629d48` succeeded, không resume. OpenClaw Dev thực thi, reviewer đúng raw diff SHA256 `5259bcec53c4c9da80855369a502b91a969186dbac4bbd3e54bae02310ade5c5`, QA riêng và host acceptance **32 passed, 1 Starlette deprecation warning**.

Commit `4a794e2b3d62247881fef4c0908eeeee9f043ba2`; [PR #9](https://github.com/Luim3141/mini-task-manager/pull/9) OPEN, stacked trên PR #8. GitHub REST read-back xác nhận SHA/base; không auto-merge. Feature `GET /tasks/{task_id}/title`: tồn tại 200, thiếu 404, invalid 422, Unicode giữ nguyên, không đổi schema. Reviewer là internal OpenClaw review, không giả GitHub native review. Demo cổng 18791 vẫn PR #6 unmerged tree, có endpoint/header TEST RELEASE; PR #7/#8/#9 chưa deploy demo.

Native #390 lockVersion2/PR link và exact knowledge citation được đọc lại; 9+13 lifecycle ACK khớp observation. On-Demand/Daily/Weekly GENERATED/READY sources CURRENT chứa child #390/PR #9, AI narrative mới `be099f56-cc9a-403c-96c2-9c958d4672dc` có hai LIVE_SUCCESS receipts gắn report ID và nhãn chưa xác minh. Không lấy exact-ID query làm semantic quality.

**Revision boundary:** coding run trên Gateway bca2ff25… / Core a6a61b68…; reporting image 8cd rồi 8359 thay cùng module sau đó, được candidate/API tests riêng. Không gọi coding E2E là whole-image E2E của 8359. Evidence raw tại `phase2-final/e2e/`, source/image parity tại `final-live-verification.json`, Project5 column-level comparison tại `native-post-e2e.json`. Sau test đã khôi phục PAUSED tạm; final 08:04 UTC đưa OFF bằng Gateway HTTP, active0/provider gatefalse. Không có fresh task thứ hai.
