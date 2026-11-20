# Playwright / Chromium E2E

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Microsoft Edge Chromium headless; real Core/Rails, signed UI bridge, Gateway, PostgreSQL Native API trên clone loopback. Login PM và BA bằng saved password/TOTP, không giả mạo actor. Không chụp credentials/TOTP.

Coverage: Assistant→Monitor và History→Monitor, historical6nodes/realdependencies, legacyBAoutput, timelinefilter, zoom/fit/compact/keyboard/highlight, replay, dark mode,375px mobile/table, historyempty/search/state/sort/pagination. Active real Supervisor/SDKMock→PLANNING/RUNNING→COMPLETED không F5; canonical BA/DEV/QA/Reviewer outputs, observedtimestamps, failure503, session expiration/replayclear, BAforbiddenPMrun, ownhistorybinding, XSSliteraltext, terminalpollstop, networkfailure/reconnect.

Actual live historical run7d528511(actor7):4recorded Gemini calls,9324tokens; không phát sinh call khi xem. New fixture451 execution là MOCK_TEST,4SDKgenerations/36recorded events; failurefixture dùng injected503.3additional localreadonlyruns làm đủ pagination. Không copy run sang actor synthetic hoặc sửa Native fixture để chứng minh ACL. Revokedmembership/version được kiểm thử bằng Native contract mock trong backend suite; không tuyên bố đã thu hồi quyền thật trên serving Staging.

Raw browser failure logs/sessionstate private. Screenshots được lưu vùng Monitor, che Native sidebar bằng neutral mask; không lộ secrets. Initial full-element screenshot bị compositor clip phần ngoài native scroller, không dùng làm visual acceptance. Viewport screenshots graph/mobile/dark là bằng chứng review.

Status/count/images authoritative trong browser-e2e.json; final serving URL acceptance chỉ chạy sau owner deploy approval, chưa có proof trên public Staging của tính năng mới.


Final:25PASS assertions (22main+3extra).20main assertions completed in the full finalimage driver;2remainingBA assertions in continuation after correcting fixture role label BA-PM, same immutableimages. Driver lookup failure retained in browser-e2e-initial-finalimage-fixture-error.json.0MonitorJSerrors;2NativeanonymousHAL errors on login/TOTP explicitly classified. Final screenshots reviewed on desktop/dark/mobile; no secret values shown. Pan/fit, CC registry-runtime-lastreceipt and replay slider also PASS.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.
