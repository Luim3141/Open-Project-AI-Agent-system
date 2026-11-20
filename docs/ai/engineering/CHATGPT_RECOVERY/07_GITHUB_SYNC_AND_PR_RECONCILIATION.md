# Phase2 current — 01/11/2026

Phase2 current: engineering_github_sync durable SQLiteoperationjournal; reserveatomic, UNKNOWNbeforePOST, stablemarkerreadback acrosspages, unknownnoautomaticrePOST, explicit4xxrejection retryable. Concurrentrequests1POST; disconnectaftercommit/crashbeforepersist reconcileexistingmarker; legacyexactnoteadopted.10journal tests use real localhostHTTPNative and tempStore; total affected182PASS. RemotePR snapshot below is historical read-only; no newpush/merge/Nativecomment. See phase2 logs and source-candidate-final-manifest.json.

---

# GitHub Sync và reconciliation

Read-only GitHub plugin `get_pr_info` xác nhận snapshot 01/11: PR1 merged vào main, PR2/3 merged vào feature branches, PR4/5/6 OPEN. PR6 head `0498ceeda97cd3e856a975129129e71f6c94a3dd`, base `codex/openclaw-health-check-v1`; không là deployment proof. Không merge/push/close PR trong recovery.

## Root causes và patch

- `ai_runs` không có payload. Mapping cũ SELECT payload từ bảng này rồi nuốt exception; nay join ai_queue/ai_runs, chỉ project6+OpenClaw+đúng repository, dùng native_readback.child_id trước parent payload379.
- Ghi activity Native lỗi vẫn trả SUCCESS/count giả; nay item UPDATED/UNCHANGED/FAILED, tổng actual changes và SUCCESS/PARTIAL/SYNC_FAILED; fetch failure cũng persist last attempt metadata.
- Trước POST đọc Native package, kiểm id/project6/parent379. PR ngoài mapping không bị gán vào parent379. Không auto-transition Done hoặc phát hành vì PR merge.
- Fetch TTL phân biệt repo, cache empty results, force fetch thật, pagination100/page với deadline20s và incomplete-collection error. Bỏ synchronous per-PR review calls khỏi status fetch; reviews/CI chưa kiểm tra ghi NOT_CHECKED, không ghi thiếu review hay CI nếu chưa hỏi GitHub.
- Rails thông báo số thật kể cả0; failures hiện @error, success toast không xuất hiện cùng lỗi. View bỏ 6-row PR fixture và ONLINE hardcode; WP link lấy projection từ backend.

## Verification

`tests.test_engineering_github_recovery`: 6 lỗi RED gốc, pagination RED và UI mapping RED đã lưu. `tests.test_engineering_github_sync` + recovery: 14 tests đạt trước integrated regression. Logs trong run directory. `check_github_ui.rb` thực thi Ruby projection/error branch, không browser; serving r24 vẫn RED do fake PR fallback, candidate source GREEN. Ruby syntax/ERB compile kiểm riêng trong candidate image.

## Giới hạn

Chưa thực thi live Sync mới/POST Native vì đang chuẩn bị candidate. Cache chỉ ngăn lặp sau successful known result, không bảo đảm exactly-once khi process crash sau POST trước persist hoặc concurrent calls. Unknown Native outcome cần reconcile, không blind retry; REC-018 vẫn mở. Không tuyên bố trạng thái Native WP384/386 đã được reconcile khi mới sửa source. Link PR state khác deployment/Owner acceptance.
