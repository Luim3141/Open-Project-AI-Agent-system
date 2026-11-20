> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# SOURCE RUNTIME RECONCILIATION

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

Đã phân loại đủ35module thiếu và7module khác phiên bản của lần takeover. `SOURCE_RUNTIME_MATRIX.json` giữ SHA lúc phát hiện và quyết định từng module; `candidate-runtime-parity.json` là SHA source/image hiện tại.

35module runtime/internal được đóng gói, import và kiểm tra hash;7prototype/dev được loại có chủ đích trong `.dockerignore`: e2e_demo,intent_evals,supervisor_isolation,n8n_indexing_hook,proposal_aggregation,proposal_ux,scheduler_registry. Không copy hàng loạt prototype vào service.

Build bằng `tests/qualify_remaining.py --build-gateway` và `--build-core`, dựa trên hai base image đang phục vụ được giữ nguyên bằng tag riêng. Recipe: automation/RemainingGateway.Dockerfile và DailyCore.Dockerfile. Candidate chỉ COPY source đã xét; không migration. Core7file được kiểm tra bằng `core-package-parity.json`; CSS nằm trong ERB, JS upstream giữ nguyên.

Serving Gateway006b9c6c/Core8a42c7ef vẫn chưa được thay. Source/candidate đã reconcile; public runtime chờ owner approve. Không reset/stash/clean/add-all/push Git; native fork hiện hữu không sửa trong đợt này.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
