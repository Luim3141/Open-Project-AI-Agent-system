# Phase 4 — implementation deployed, functional acceptance PARTIAL

13/11/2026 Asia/Bangkok, branch `codex/agent-studio-v2-stabilization`, baseline `f3b713a`. Single agent, headless browser only. Source commit reference in [handoff](HANDOFF.md). Existing data/history/docs retained.

| Gate | Verdict |
|---|---|
| RAG | PARTIAL — retrieval25/36; actual grounded Web + real Telegram positive PASS |
| GATEWAY READ | PASS for22tools + actual scopedMCP/semantic reads |
| GATEWAY COMMAND CONTRACT | PASS isolated auth/approval/idempotency/fencing tests |
| MAIN LIVE MUTATION | BLOCKED BY AUTHORIZATION / NOT TESTED |
| COMMAND CENTER | PARTIAL —15UIgroupsPASS, controls not all live-exercised |
| SYSTEM FUNCTIONAL | PARTIAL |

Đã sửa và triển khai11productfiles: registered sources chung searchNative theo quyền/pin; fullchunk citation và boundedhybridranking; longliteralreference priority; explicit Gemini answer với exact quote validation; postgenerationACL/source recheck; typed outage/abstention; Telegram read-onlyRAGturn/technicalcitations; Rails caller/UI mode/clearabort/raceguard/deadline110s/wrap. Search/extract không hiddeninference. Model/key/caps/gates không đổi, không dependency mới.

FinalOwnerTelegram41→42: câu hỏi tài liệu được đọc RAG trước model, có sourcepin/checksum trong footer, trả lời đúng nội dung/khôngOwneracceptance,1resolvedexact3.5litecall. Lượt39→40 trước bản sửa đã tái hiện memoryreuse không freshRAG và được giữ làm failure proof. Bản cuối67Bot testsPASS; quota ngày20770 tự nhiên2/20, không reset/tăng cap (ngày20769 vẫn20).

MAINWeb trả lời đúngfixturepurpose và “does not certify … Owner acceptance”, citations/source pinreadback đúng. No-answerMars đầu tiên503→ABSTAIN_PROVIDER; sau khi provider hoạt động lại, một negativequery mới nhận actualmodelABSTAIN/resolvedexact3.5lite. Gold40 (8cal/32holdout),36retrieval realBGE/Qdrant/privateconsistentSQLite:8/36baseline→25/36final (holdout19/28), naiveextractfacts20/36; không coi là40Geminianswers hoặcFULLRAGPASS.

Gateway:29Bottools/22reads/7writes,15RESTpaths,87MCPtools visible currenttoken; exactactualidentity18/P6verified. ReadDTOsemantic:398AwaitingOwner/currentagentnull, globalactive0/OFF, checkpoint27=11steps. Controls chỉ có isolatedcontracts; không executeMAINmutation. CommandCenter9tabs, runinspector, Reportsraw/export, Studio3nodes/artifacts/Back/reload, RAGanswer/read vàvisiblemobile đã kiểm; everybutton coverage không được giả.

Regression Gateway466run/22skip=444passed; finalBot67PASS, NodeVMtransportPASS, RailsErubiPASS. Data/config/index before/after13checksPASS và sourceparityCore82/GW115/Bot10. Task398v10/catalog14/PR15OPEN/OFF preserved; n8n/pairing/outbox unchanged; old620receiptrows immutable,8authorizedRAGreceiptsnew. NoAgentRun/newTask/approval/merge/productPRdeployment/DBrestore/reindex/volume deletion.

Deployed images:

- gateway: `sha256:26bfcdbef5d2ff8bbc0b64195a7c8e6750391dce84731f45fa52ea26cffa2ad1`
- core: `sha256:113472c4ec1d0ab1796a55199bcb27ce935fc982b9c1047049318a20395b16ba`
- telegram: `sha256:828cfb8a73dc2752c3232be46030fc6e4f80b46cc61826527d7f00fbe96efab2`

Rollback image-only using guarded release private manifests; keep currentDB/catalog/history/volumes. Baseline Core7923304/GW6edeea/Bot334963 retained, prior scopedrelease manifests preserve immediate rollback images. New runtimeproviderreceipts never erased through oldDBrestore. AI_IMAGE/CORE_IMAGE/bridgepins only; .env blank-line rewrite noted with exactsemantic backup proof, keys/configvalues unchanged. No push.

Reports: [RAG audit](RAG_AUDIT.md), [evaluation40cases](RAG_EVALUATION.md), [Gateway29matrix](GATEWAY_TOOL_MATRIX.md), [CommandCenterinventory](COMMAND_CENTER_MATRIX.md), [E2E](E2E_RESULTS.md), [bugs](BUG_FIXES.md), [regressions](REGRESSION_RESULTS.md), [data](DATA_INTEGRITY.md), [remaining](REMAINING_ISSUES.md). Source/API changes add optionalmodeonly; searchdefault compatible. Detailed inputschemas, sourcepins, actualfailures/correlationIDs and screenshots accompanyreports; private secrets/cookies/DB excluded.

Chưa kiểm: mọi livewrite, bulkGeminianswerquality và p95. Rủi ro còn lại: semanticmisses/provideravailability và intent không rõ ràng còn phụ thuộc modelrouting; toàn hệ thống chưa FULL PASS.
