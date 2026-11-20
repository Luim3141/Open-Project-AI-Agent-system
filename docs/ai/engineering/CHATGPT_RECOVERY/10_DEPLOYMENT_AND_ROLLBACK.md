# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `rollout-20261101T110426Z/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

# Phase2 rollout / rollback — PREVIEW ONLY

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

| Service | Candidate tag | Exact image ID |
|---|---|---|
| gateway | `qldapm-ai:recovery-phase2-20261101-r2` | `sha256:1c10248134b4f7973685433a9686f3d841ed96e5b767dd5b7d497adc0e3eceeb` |
| core | `qldapm-core:recovery-phase2-20261101-r1` | `sha256:c237e4a792608e5ff5b95a7c9c36d41dc0392ceb3ec07f451fbee0d96dca06c9` |
| n8n | `qldapm-n8n:recovery-phase2-redacted-r2` | `sha256:9e8d3393ca28a6603f3890218aeb3bb280952262c134e230b033380a2fd54e32` |

Serving rollback: Gateway fcb44c49afb99efd85b4a00297a58e7c5a59d36ab2f2b78e15a6a6d135f5e93e; Core a4fa8150728bc5fc50f8afed22fce898cc52065a55ff0fdb53b803a81d9e1c6b; n8n dd580fe1ab6e99e85bc66f2acf8bc8c5e9409fbe61b2e2803c5024403ef52833. Phase1 candidate r2/r1 are superseded for this rollout; exact Phase2 IDs above are authoritative.

Single approval proposal `phase2-20261101T050128Z/rollout-proposal.json`, SHA256 `30218aff60ff98c0c92c0858c6f0ca77c11e9f6e4b216176843069ed46de92d9`. Expected affected scope: Core/Gateway/n8n availability during recreate and Windows delivery worker while stopped. Clone startup is not a downtime guarantee; allocate maintenance window and health timeout, stop on any mismatch. Preserve data, ports, env, provider/model/quota, owner/TOTP/encryption configuration. No DB service restart/migration or volume deletion.

After exact approval only:

1. Re-read runtime/source/image/WF04activeversion; OFF/active0/worker no active unit; Project5/379/unknown receipts unchanged. Create fresh consistent private backups ofPG/Gateway/knowledge/configs **and n8n data/encryption configuration**. Confirm restore artifacts; if state drift, reconcile before applying.
2. Stop only QLDAPMEngineeringDelivery after idle check. Keep immutable source snapshot and prior worker+engineering_delivery backups. Current host source already changed, old loaded process unverified; restart is required to load reviewed code.
3. Replace n8n image preserving private before Config/HostConfig/Mounts/network/ports in `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\phase2-rollout-preview-5cb95f3e`. Target only WF04 `elfapV5D2PTnLiHW` with compare-before activeVersion `4a8ddd7c-763a-45dc-adb1-99633047b62e`. Private candidate preserves4oldnodes/connections and adds4; use targeted supported n8n CLI import/publish while service stopped, no bulk16workflow import. Keep prechange workflow private for rollback. No historical prune/tokenrotation. Verify startup/canary metadata without exposing realcredential values.
4. Generate private64hex lifecycle signing key and set n8n_lifecycle enabled/url for fixed local `/webhook/qldapm-lifecycle`; keep config copy/permissions. Callback Host localhost:18089 is already allowed; no Host/security guard expansion. Apply only gateway/web images with the existing Compose prefix + candidate overlay; no --build or dependency rollout. Commands below are **not executed**.

```powershell
docker compose -p qldapm-ai --env-file "$env:LOCALAPPDATA\QLDAPM\openproject-ai\.env" -f openproject/ai/compose.yml -f openproject/ai/gemini-free.main.yml -f docs/ai/engineering/CHATGPT_RECOVERY/compose.gateway.candidate.json up -d --no-deps gateway
docker compose -p qldapm-openproject --env-file "$env:LOCALAPPDATA\QLDAPM\openproject\.env" -f openproject/compose.yml -f "$env:LOCALAPPDATA\QLDAPM\openproject\ui-bridge.yml" -f docs/ai/engineering/CHATGPT_RECOVERY/compose.core.candidate.json up -d --no-deps web
```

5. Re-read exact images/15hashes/health, hosts/RBAC, Project5/379 baseline, receipts/queue; start exact Windows task only after hashes match; verify heartbeat/process start after source version. Keep engineering OFF. Authenticated read contracts/reports/RAG and idleoutbox/n8n status next. Fresh business E2E withprovider/GitHub/Native writes needs bounded scope authorization, not implicit in code rollout. Owner UI UAT remains separate.

Rollback: hold OFF/stopidleworker; disable lifecycle config to stopdelivery, preserve outbox/error receipts; restore WF04 exact previous graph/settings; use same Compose commands with compose.gateway.rollback.json / compose.core.rollback.json, restore n8n previous image **with same volume/config/encryption**. Revert host worker and engineering_delivery from reviewed backups if required, then startidle task and readback invariants. Do not restore oldbusinessDB, resetvolume or erase unknown outcomes. Additive SQLite journal/outbox tables may remain; oldimage ignores them. Clone Gateway/Core rollback health tested, not live traffic cutover; n8n originalimage remains available, data downgrade effects require preflight against freshcopy.
