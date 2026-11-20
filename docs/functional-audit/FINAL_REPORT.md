# QLDAPM — Functional audit & recovery, 12/11/2026

**Kết quả tổng thể: FUNCTIONAL PARTIAL.** Đã sửa và triển khai các lỗi có bằng chứng F1–F5. Các lượt Telegram, read paths và UI nêu dưới đây đã được xác minh; chưa đủ điều kiện tuyên bố toàn bộ hệ thống FULL PASS.

## Đã thực hiện

- Sửa bot kết luận DONE sai khi Task còn chờ Owner; phân biệt checkpoint revision27 với11 bước đã hoàn thành. Owner kiểm thử lại qua Telegram và nhận câu trả lời đúng.
- Bổ sung3 read tools dùng Observer hiện hành cho active agents, blocked tasks và pending approvals; giữ project scope, freshness và giới hạn nguồn. Lượt Owner35→36 gọi `get_active_agents`, nhận tool result rồi trả lời đúng toàn project6, không còn vòng lặp ở lượt này.
- Thu gọn global read DTO: pending approvals từ443357B xuống8660B, không còn context truncation trong snapshot kiểm thử. Không bỏ acceptance/blocker/source bounds; artifacts đọc qua detail tools.
- Sửa Core giữ HTTP status, Retry-After và requestID của upstream thay vì mask thành503. Malformed/negative execution offset trả422 trước khi gọi Gateway; MAIN đã kiểm chứng.
- Kiểm kê206 dòng chức năng,17 workflow n8n và29 Telegram tools. Có52 dòng PASS ở mức bằng chứng ghi trong ma trận,70PARTIAL,30NOT TESTED và54BLOCKED BY AUTHORIZATION; đây là coverage của audit, không phải tỷ lệ hoàn thành sản phẩm.

## Bằng chứng kiểm thử

| Phạm vi | Kết quả |
|---|---|
| Gateway isolated contracts | 423 tests run:401pass,22skip; exit0 |
| Telegram / host / Node workflow | 62 /12 /6 tests PASS |
| Core candidate | Ruby status, retry hints, requestID và invalid-offset contracts PASS |
| MAIN semantic reads | 13 assertions TRUE;18 original adapters +3 global reads;4 existing-record reads bổ sung |
| MAIN UI | 14 nhóm PASS,0 JS errors;9 tabs,6 roles, loaded RunInspector, report render/raw/export, RAG citations, Studio graph/artifacts/Back/reload |
| MAIN final smoke / integrity | 6 /21 assertions TRUE |
| Telegram thật | Owner32/34 đúng acceptance/count;35→36 đúng global active agents; actual resolved model `gemini-3.5-flash-lite` |

Gemini daily budget18/20, giữ lại2 calls; không reset/increase cap. Metadata check cuối xác minh đúng model, bot CONNECTED, webhook không cấu hình, actor18 có identity project5/6; không chạy inference thêm. Sau restart, health chỉ báo CONFIGURED_UNVERIFIED cho readiness của process mới; không gọi metadata là inference proof.

Một lượt RAG UI trước đó không hiện results; probe kế tiếp200 khoảng11giây và full UI rerun PASS. Screenshot Studio sau burst có Explorer429 dù graph đã tải; probe riêng sau đó tải19Task với list/graph200. Chưa xác định nguyên nhân lượt RAG lỗi hoặc chứng minh mọi burst đều phục hồi; các trường hợp này vẫn nằm trong remaining issues.

## Source và triển khai

Source commit **`8ccd793e47a30afe71eae4d52e829e2737dca541`**, local trên branch `codex/agent-studio-v2-stabilization`, base`ee4bcf8`. Chỉ4 product files đổi: Core controller; Telegram engine.py, tools.py, system_instructions.py. Tests, architecture và checkpoint đi cùng; không push remote.

| Service | Image MAIN sau audit |
|---|---|
| Core | `sha256:7923304bab831598957760c50011884bb3156b5baa431e0e99ad0439221841d8` |
| Telegram | `sha256:3349636541d4cccaba044d40bcf3f25dcfd469d5cf7419a9ff3c39aa7b2437e7` |
| Gateway — giữ nguyên image/source | `sha256:6edeea411e079bb8b2cb8242b4a79673cd74734943536e965d69bbbfbd61cef0` |
| n8n — giữ nguyên container/workflows | `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269` |

Controlled rollouts chỉ thay image, Core đi cùng restart Gateway; bot restart riêng. Config/keys/model/caps/gates/volumes giữ nguyên; không restore DB. [Bot deployment](bot-deployment.json), [Core deployment](core-candidate-v2/deployment.json), [source/data integrity](integrity-final.json). Rollback bằng exact prior images, giữ dữ liệu và catalog14.

## Trạng thái bảo toàn và giới hạn nghiệm thu

Task#398 vẫn Nativev10 READY FOR RELEASE/AWAITING_OWNER_APPROVAL; historical Nov6 BA/PM→Dev→Reviewer→QA có64tests, PR15OPEN. SupervisorOFF/active0, catalog14, engineering provider receipts620; không tạo Task/run mới, approve398, merge/deployPR15 hoặc thông báo hoàn thành sai. Native projects/roles/workflows, critical run/checkpoint tables, pairing/outbox/context và17n8nworkflow/credentials giữ fingerprints trước/sau.

Historical #397 completion16→OwnerReply19 giữ đúng context397. Current outbox7SENT; không gửi proactive message mới. RAG lexical retrieval/citations và Native ACL/version hoạt động, nhưng semantic answerability chưa đạt gate. GitHubPR15 có0 remote CI checks/0 human reviews trong snapshot: local AIReviewerPASS và JUnit64 không thay thế remote CI. Các live mutation và nhiều n8n branches chưa chạy mới; không dùng history/fixtures giả làm fresh E2E.

Chi tiết: [ma trận chức năng](FUNCTIONAL_MATRIX.md), [E2E](E2E_RESULTS.md), [root cause và fixes](BUG_FIXES.md), [regression](REGRESSION_RESULTS.md), [bảo toàn dữ liệu](DATA_INTEGRITY.md), [chưa nghiệm thu](REMAINING_ISSUES.md). Evidence giữ RED và các lỗi ban đầu. Performance campaign được hoãn theo yêu cầu.
