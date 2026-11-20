> Current 2026-10-18T21:50:12.893792+07:00: **STAGING_DEPLOYED_VERIFIED**; owner approval/apply/real5role readonly UI+Supervisor/power recovery in STAGING_DEPLOYMENT_REPORT.md. Nội dung qualification dưới đây giữ scope/version lịch sử; câu “NOT_DEPLOYED/BLOCKED_OWNER_APPROVAL” bên dưới là trạng thái trước rollout, không yêu cầu deploy lại. G2/Main/TOTP gates giữ nguyên.

# QUICK TUNNEL REPRODUCIBILITY

Updated: 2026-10-18T17:23:52.679063+07:00

**VERIFIED trên clone/candidate — QUALIFIED_NOT_DEPLOYED. Serving deployment: BLOCKED_OWNER_APPROVAL.**

Candidate Gateway: `sha256:6afb78c4576c1c5a319fb522a460465d4d7e8cc1daa41988efdb6401f0d56fea`. Core: `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99`. Phiên này không gọi Google.

RD05 VERIFIED bằng kiểm tra read-only và sửa metadata; không restart/fault public tunnel.

Image đang chạy `sha256:a80f54e29918ec66c82cdc7ad8fd9a65e3082e59825c0356d5737916959884c6` được đối chiếu với bản rebuild `sha256:eb4cb5b6f52946912fec82300c8a79df44059081d1c99710948fe0ca133d95df`. Binary/script SHA, version cloudflared2026.10.0, RootFS/entrypoint khớp; image ID khác metadata. Nguồn vendor digest được pin trong QuickTunnel.Dockerfile.

Saved stage-runtime manifest trước đó trỏ nhầm vendor binary; đã backup private và sửa atomic duy nhất image/script metadata sang wrapper thực tế. Compose có default immutable; provision giữ image đã lưu. Không thay containerID/StartedAt/RestartCount/URL.

Không secret mount hoặc Docker socket; read-only root, mạng front riêng, unless-stopped. Supervisor kiểm tra edge /ready; không thực hiện lại fault injection vì chưa được owner duyệt. Landing/URL synchronization giữ cơ chế cũ. Quick Tunnel URL vẫn có tính chất ephemeral.

Bằng chứng: quick-tunnel-reconciliation.json, quick-tunnel-reconciliation.log, operator-status-after-tunnel.json và serving final snapshot. Không chạy provision rộng để tạo bằng chứng.


Final proof:520Windows tests,30Linux image tests,64browser checks,13Control Center/cancel/CSRF checks,5concurrent browser outputs,42module+7Corefile parity. UAT_TEST_RESULTS.csv ghi riêng scope/version; không cộng gộp mock thành live Gemini.
