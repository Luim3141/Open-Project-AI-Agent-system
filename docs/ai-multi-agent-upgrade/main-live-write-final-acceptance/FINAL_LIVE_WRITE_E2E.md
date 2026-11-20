# QLDAPM MAIN — Live Gemini Write Acceptance

Ngày chốt: 22/10/2026, Asia/Bangkok. Verdict: **MAIN_LIVE_GEMINI_WRITE_E2E_PASS — sau Native reconciliation**.

Đúng một request Gemini Live từ browser PM19 đã yêu cầu Business Tool tạo đúng một **[Subtask #367 `test`](http://localhost:8088/work_packages/367)**, Project5, Type10, Parent50, QA23, trạng thái NEW. Native API của PM19 và QA23 cùng đọc lại được; browser xác nhận subject/type/parent/QA/author/activity. Không dùng proposal cũ hoặc tạo riêng bằng Rails để giả bằng chứng Gemini.

Gateway hiện tại: `sha256:4322e8d3154b165e2e6dd98c41428eec0b4a230344c7d022a73efae201a6aa7d`. Core: `sha256:5abec112e69971c9d9a58964fccf717a324a75b96b0d9f83fa7861f66eb7e449`.

Run: `6276720c-d6f8-4c3a-bf64-1e4fca623eb0`. [Kết quả Web thật](http://localhost:8088/projects/qldapm-local/qldapm-ai?run_id=6276720c-d6f8-4c3a-bf64-1e4fca623eb0). Browser Edge/Chromium qua CUA, dùng session PM đã đăng nhập; không lấy TOTP, cookie hoặc tạo phiên giả. Form thật: engine=gemini, checkbox WRITE=true, scope=50; request ID do form hiện hữu sinh. Bằng chứng: `ui-request-before.png`, `live-run.json`, `provider-audit.json`, `ui-reconciled-run.png`, `ui-native-367.png`.

## Diễn biến và giới hạn phải giữ nguyên

Native POST trả **201 sau 55.766 giây**, vượt timeout HTTP 30s cũ. Database đã commit #367 nhưng worker nhận lỗi kết nối; generation thứ ba chỉ tìm kiếm để kiểm tra, sau đó bị chặn trước HTTP thứ bảy. Tổng worker 97.865s, 6 Google HTTP/3 generateContent, không retry CREATE, không gửi request Gemini thứ hai. `native-create-timing.log` chứng minh 201, `live-run.json` giữ nguyên lỗi ban đầu.

Đã sửa tối thiểu, qualify và deploy riêng Gateway: Native CREATE dùng thời gian còn lại trong deadline 90s hiện hữu; reconcile chỉ chấp nhận đúng một source marker, author, project, type, parent, subject, description và assignee. Không có POST/PATCH/DELETE Native trong recovery. Recovery Main được operator gọi qua Core signed bridge, KHÔNG mô tả là browser bấm hoặc model tự khôi phục. `reconciliation.json` ghi route/correlation; receipt gốc đã `done`, không còn request pending.

UI hiện xác nhận “Native đã xác nhận sau timeout”, dẫn tới #367. **Worker lịch sử vẫn `failed_or_unknown`; UI là `partial`, không có bản tổng hợp model mới.** Không sửa lịch sử để biến worker thành success. Bản timeout/recovery hiện tại được kiểm chứng bằng unit, SDK mock, Native clone và recovery GET trên Main; KHÔNG gọi thêm Gemini để tái nghiệm thu CREATE trên image mới.

## Các ca nghiệm thu

| ID | Expected | Actual / phương pháp | Kết quả | Evidence |
|---|---|---|---|---|
| E2E-01 | PM thật, WRITE/scope50 đúng, submit một lần | Browser Main → Rails session/CSRF → signed bridge → Gateway, một run mới; không 403/422 | PASS | ui-request-before.png, armed.json, provider-audit.json |
| E2E-02 | Provider thật trong chính business request | 6 LIVE_SUCCESS/HTTP200, 3 generations, usage thật; production không có mock hook | PASS live | live-run.json, provider-audit.json |
| E2E-03 | Một Native CREATE đúng các trường | #367 do PM19, source marker khớp Owner claim/Gemini tool intent, một POST201 | PASS sau reconcile | native-source-proof.json, native-create-timing.log |
| E2E-04 | Readback Native và UI | PM19 + QA23 GET367; browser subject/type/parent/QA/activity đúng | PASS live UI/API | native-readback.json, ui-native-367.png/.txt |
| E2E-05 | Đúng approval policy | Direct routine write đã được Owner duyệt và checkbox đúng; không có proposal mới | N/A proposal; PASS policy | armed.json, provider-audit.json |
| E2E-06 | Run/tool/actor/scope/receipt/audit liên kết | Run claim → create key/source marker → Native367 → reconcile audit; UI hiển thị receipt đã xác minh | PASS sau reconcile | provider-audit.json, reconciliation.json, ui-reconciled-run.png/.txt |
| E2E-07 | BA/QA/Reviewer vẫn read-only | Kiểm tra stored Main run23353d1f…: done/local/model_used=false, BA/QA/Reviewer; focused regression offline | PASS stored/deterministic; không live Gemini mới | provider-audit.json regression, recovery-windows-green.log, recovery-linux-tests.log |
| E2E-08 | Giữ dữ liệu cũ, trừ Native rollup xác minh | 329→330 Project5, 366→367 global, children5→6; 267 duration derived được Native tính lại, các trường cũ khác nguyên; Sprints/Versions/relations/RBAC/TOTP nguyên | PASS với ngoại lệ Native đã nêu | integrity.json, native-duration-proof.json, final-verification.json |

## Source, build và tests

Diff thực từ Gateway e57d07d…: `source.diff`. Runtime thay đổi đúng năm file `openproject/ai/gateway/ai_worker.py`, `gemini.py`, `business_acceptance.py` (mới), `native.py`, `service.py`; thêm `tests/test_business_acceptance.py`, `tests/test_native_create_recovery.py`. Caller/get_ai_run và error/projection regression đều được kiểm tra. Core UI/source không đổi. `architecture.md` được bổ sung theo thay đổi.

- Image tạo request Live: **5cbf4ab7…**; current **4322e8d3…** là bản recovery, 54 file packaged khớp source/image/runtime; 7 prototype/dev file tiếp tục bị `.dockerignore` loại có chủ đích.
- Milestone budget: 54 test executions Windows +54 Linux PASS, exit0; actual worker + Native clone tạo một fixture #369 (331→332), SDK MockTransport 6 phases/3 generations. Không phải Google live.
- Milestone recovery: **60 test executions Windows +60 Linux PASS, exit0**; clone-recovery chỉ GET, không thêm fixture, không gọi Google. Missing/duplicate/mismatched source/author/fields và revoked visibility đều fail closed; 429/503 không retry được thử bằng SDK mock.
- Test red/green và lỗi harness ban đầu được giữ, không che: `recovery-red-corrected.log`, `recovery-focused-green.log`, `recovery-windows-green.log`, `recovery-linux-tests.log`; harness đầu thiếu PYTHONPATH, dừng trước thao tác Native.
- Build từ `openproject/ai/Dockerfile`, command trong `qualify.py`/`qualify_recovery.py`, logs giữ nguyên. Git branch `codex/local-multi-agent-upgrade`, HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`; không commit/push/reset/clean các thay đổi có sẵn.

## Vận hành và bàn giao

18 serving containers hoạt động; 17 container ngoài Gateway giữ ID/image/StartedAt, bao gồm Main Core/database, Stage/tunnel/n8n/CSDLDPT. Ba clone được dừng, dữ liệu giữ. Config/credentials/key/model/Free-only proof/RBAC/TOTP không đổi. One-shot envelope đã archive, durable claim/receipt còn nguyên: **không rearm hoặc gửi lại prompt**.

Backup online trước CREATE: `backup-20261021-235349`; trước recovery: `post-create-pre-recovery-20261022-001046`, dưới private operator directory. WAL backup thực hiện trong Linux; Windows chỉ đọc snapshot immutable. Không restore Main. Nếu cần rollback ứng dụng, dùng immutable image5cbf4ab7… (trước recovery) hoặc e57d07d… (trước đợt này), cập nhật đúng AI_IMAGE/image-lock và chỉ compose up gateway sau kiểm tra; **rollback image không xóa #367**. Native compensation/delete cần phê duyệt riêng, không tự khôi phục toàn database.

Còn giới hạn: bản tổng hợp model của worker đầu không hoàn tất; timeout90s mới chưa được chạy lại bằng Google (giữ ngân sách Owner). Billing Console không được xác minh lại: giữ Free-only theo chứng thực Owner và guard đã lưu. Không làm capacity20/nghiệp vụ khác/SecondBrain/n8n/tunnel/Sprint hoặc thêm tài khoản.

Identity discrepancy được ghi rõ: Owner gọi QA23 là `qa-tester`; Main thực tế có login `qa`. Thao tác luôn bind đúng explicit User ID23 và Native role QA, không đổi tài khoản. Bằng chứng `identity-and-counts.json`; không mô tả `qa-tester` là login đã được xác nhận trên Main.
