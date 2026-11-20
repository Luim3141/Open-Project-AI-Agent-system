> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# UAT TEST PLAN

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Môi trường bắt buộc: owned isolated clone,5new fixtures, no provider key/no Google, Native project3 cố định. Không chuyển fixtures sang Staging đang phục vụ.

1. Mỗi role: Native login/TOTP/actor, Control Center, Supervisor từ form thật, queue/process/plan/text/trace, own knowledge ingest/search/citation,390/1280, logout và session denial. PM preview/create/update; non-PM deny update và forged actor.
2. Canonical proposal: no-write preview, wrong actor/hash, confirm/native readback, replay denied, stale denied; comments5roles. Native direct BE patch403, invalid status PM422; HMAC invalid/valid/replay403/200/403.
3.5concurrent actor admissions và real worker outputs;5browser results đồng thời. Không dùng20user.
4. Knowledge: dedup/update/stale-hide/reindex/deindex/actor isolate, real2-project membership deny, physical FTS/chunks restore, restart/corruption fail-closed, existing4document cold compatibility.
5. Control Center: >10own runs, cancellation queued, no Native version change, paging10/disjoint next/previous, filter empty, sort, refresh, responsive, missing CSRF token đúng form action.
6. Build/hash/import/startup/Native compatibility, regression/security contracts, n8n signed status/daily and error contract, backup/restore/old Gateway compatibility/resources, serving before/after check.

UAT_TEST_RESULTS.csv là bảng caseID/expected/actual/status/exit/evidence/version. Mocks, prior image cases và live Native/browser được ghi tách scope. Failure cũ giữ làm lịch sử; chỉ dùng rerun có bằng chứng để đóng lỗi. Live Gemini, public fault, Main promotion, TOTP rotation và20-user không được tự chạy.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
