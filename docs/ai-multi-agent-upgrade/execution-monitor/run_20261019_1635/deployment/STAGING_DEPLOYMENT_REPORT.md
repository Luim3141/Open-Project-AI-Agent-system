# Execution Monitor đã hoạt động trên Staging

**COMPLETE_ON_STAGING — 2026-10-19T20:01:45.802306+07:00.** Đã triển khai đúng preview owner duyệt: Gateway456c38f6, Core7d76c1eb và reload local-backup hiện hữu. Không cần deploy lại.

Mở [Lịch sử xử lý / Execution Monitor](https://buried-glad-rpg-recall.trycloudflare.com/projects/qldapm-local/qldapm-ai/executions) và đăng nhập bằng tài khoản hiện có. Trang http://localhost:18090 luôn hiển thị URL Quick Tunnel hiện tại.

30 ca Playwright/API công khai PASS với PM, BA, FE, BE, QA: login/TOTP/logout, Assistant/Control Center, history theo actor; graph6node/output/timeline/replay/mobile; hết phiên và chặn đọc chéo run bằng API403/UI. Source/image/runtime khớp51fileGateway và47fileCore. Qualification trước deploy:196testsWindows,127testsLinux,25ca browser trên clone. Không coi mock là Gemini live.

18container healthy;15container ngoài phạm vi giữ nguyên ID/image/starttime. Main/CSDLDPT, Quick Tunnel, n8n và database không bị restart bởi apply.372WorkPackages, mật khẩu, cấu hình TOTP, RBAC/nativegates và SecondBrain được giữ;9fileprivate không đổi. Sau UAT chỉ4bảng auth metadata đổi đúng dự kiến; mọi thuộc tính bảo mật của12users/28TOTPdevices giữ nguyên. LedgerGemini517→517; không có Googlecall mới hoặc Nativebusinesswrite.

Backup mới trước deploy đã restore221bảngPG/assets/config+3SQLite. Backup sau deploy61266765-03f3-459c-b7b1-a96f4a656591 đã restore3SQLite; run/output/proposal/audit/receipt cũ giữ nguyên. Image-lock/manifest/restartpolicy đã lưu; Gemini dùng lại key/policy hiện có.

Giới hạn: run cũ thiếu agenttiming/Revieweroutput riêng nên UI ghi rõ dữ liệu thiếu. Không gọi Gemini mới, không restartDockerDesktop thêm, không test20người hay promoteMain. QuickTunnel có thể đổi hostname sau lần khởi động Docker tiếp theo.

---

Chi tiết và bằng chứng kỹ thuật:

# Execution Monitor — COMPLETE_ON_STAGING

2026-10-19T19:59:52.412347+07:00. Owner approved exact preview SHA256 `61e1719f8baea3c9c90dffd07deb577e86ae182673324aedc8d943eab7870527`. Application-only apply succeeded; 30 serving browser/API assertions PASS for PM/BA/FE/BE/QA.

Access: [https://buried-glad-rpg-recall.trycloudflare.com](https://buried-glad-rpg-recall.trycloudflare.com) · [Run History](https://buried-glad-rpg-recall.trycloudflare.com/projects/qldapm-local/qldapm-ai/executions). URL changed during Docker startup **before** this deployment; QuickTunnel ID/image/starttime remained unchanged during apply. Local landing http://localhost:18090 always shows current QuickTunnel URL.

Serving Gateway `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`; Core `sha256:7d76c1eb8ad8e352c7daabd467d032cddba654536bc2ca5a89d9a36e9b138d20`.51Gateway/47Core source hashes match image/runtime; manifest/image-lock updated and restartpolicy unless-stopped. Saved FreeOnly Gemini policy/key revalidated locally; no Googlecall or billing/model change. No new DockerDesktop restart after deploy.

Scope applied:2appimages replaced; existing local-backup watcher reloaded with same image/containerID.15other servingcontainers retain ID/image/starttime.18healthy. Initial preflight detected preexisting wholeDocker startup on oldimages, no partialapply/no oldoperatorprocess; waitedhealthy and took freshbaseline before mutation. Apply command36seconds; exactHTTP downtime was not measured, approved window2–5minutes.

UI/API actual:5real accounts logged in with unchangedpasswords/TOTP and logged out; Assistant/CC/navigation/ownhistory available; PM viewed savedGemini6nodegraph,4assignment/6dependencyedges,BAoutput,timeline,replay,mobile375 andhistoryemptyfilter.4nonPMroles receive403 for PMrun via directAPI and empty protectedUI; expiredsession/replay clearscontent. No operator/shell/write_code in Business Assistant.

Historical run7d528511 actor7 remains LIVE_GEMINI from actualsavedreceipts:4calls/9324tokens. No execution replay/modelregeneration. New active/failure lifecycle andcanonical4outputs inclReviewer were qualified on exactimages via realSupervisor/Native +SDKMockTransport, not called on servingGemini. Prior qualification196Windows/127Linux/25clonebrowser checks, not rerun as liveGoogletests.

Preservation: all221Native fingerprints equal immediately after apply before UAT. After5roleUAT,217remain exact; only users(last_login_on/updated_at), TOTPdevices(last_used_at), sessions andsequences differ. Archive-vs-current comparison confirms all12users and28TOTPdevices keep every otherfield including credentials/devicekeys/active/default;9privatefiles byte-identical.372WP andbusinessrecords unchanged; noMainpromotion/CSDLDPTchange/nativebusinesswrite. Gemini ledger517→517, noactivequeue, SQLitequick_checkok. All oldruns/tasks/outputs/proposals/providerreceipts/auditrows retained;SecondBrain documents/chunks unchanged.

Backups: freshpreapply a6128654-1af4-4086-8d41-68c094eb3216 restored221PGtables+assets/config and3SQLite. Postapply `61266765-03f3-459c-b7b1-a96f4a656591` restored3SQLite withlogicalhashes equal; Native/auth/config/privatearchives retained. Rollbackpair40cb/Core3b remains documented and oldGateway additiveSQLitecompat qualified. No rollback required.

Browser diagnostics:0MonitorJSerrors;11Native HAL authentication errors during anonymouslogin/logout/expiredsession, explicitly classified,0othererrors. Raw credentials, cookies, TOTPcodes anddiagnostics private; public screenshots containonlyauthorizedMonitor UI.

Evidence in deployment/: receipt.json, post-deploy-parity.json, serving-browser.json, serving-test-results.csv, final-preservation.json, sqlite-history-preservation.json, pre/post-deploy-backup.json, pre/post-deploy-cold-restore.json, pre-deploy-pg-restore.json, browser-js-classification.json andscreenshots/.

Remaininglimits: historicalagenttimes/Revieweroutput not separatelystored andnotinvented; deterministicReviewer isnotsemanticproof. No newliveGooglecall,20usercapacity/Mainpromotion, or forcedDockerDesktop restart. QuickTunnel hostname maychange atnextDockerstartup; savedGeminikey/policy remainsreusable.
