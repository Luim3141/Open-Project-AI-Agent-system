# Bảo mật và giới hạn

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Trust boundaries: browser→Native Rails session→HMAC private bridge→Gateway actor/project→Native identity/membership/item/version→canonical records. Không cấp quyền bằng run ID, UI label, stored model content hoặc actor_id do client truyền.

Cross-actor/project, revoked item/membership, changed lockVersion và typed output scope có regression. STALE hides stored business outputs/requests/events/sources. Replay/node detail chỉ đọc, reauthorize; GET không gọi provider hay mutate Native. Business Assistant không có shell/operator tools mới.

Outputs không tin cậy: Rails escaping, JS textContent/DOM API và SVG text, không innerHTML/Markdown injection. Fixture `<script>` được render như chữ, không tạo script node hoặc chạy JS. Input query SQL bound. Source links dựng từ positive Native work-package IDs, không dùng URL do model cấp.

Event schema allowlist và safe error identifiers; không log key/TOTP/cookies/provider raw payload/CoT. Credentials/raw diagnostics nằm private operator directory; public proof chỉ sanitized summaries/schema/IDs/screenshots đã kiểm tra. Stored canonical outputs vẫn chịu safe_text hiện hữu và Native scope checks.

Quota/billing/model/saved key không đổi. Gemini.enabled=false + synthetic key trên clone, SDK MockTransport explicit. Serving ledger517 before/after.5Gatewayprivatefiles và Nativeprivatearchive khớp verified backup ba33. TOTP_NOT_APPROVED_DO_NOT_ROTATE.

Giới hạn: browser đã nhận dữ liệu không thể thu hồi khỏi trí nhớ người dùng; fail-closed áp dụng khi request/replay/node/visibility revalidates. Không có push ACL revocation. Poll3s có độ trễ; terminal không poll nền. Không claim kiểm toán lại113tasks, semantic correctness toàn bộ output hoặc zero-cost độc lập Google Console.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.
