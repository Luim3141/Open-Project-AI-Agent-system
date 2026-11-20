# Provider và audit evidence

Run `6276720c-d6f8-4c3a-bf64-1e4fca623eb0`, authenticated PM19, Project5, scope[50]. Gemini model `gemini-3.5-flash-lite`, cùng key/project `gen-lang-client-0020540057`; Free-only, billing=false và không paid fallback theo cấu hình Owner đã chứng thực. Không gọi API Billing/Console và không cam kết kết quả kiểm tra billing live.

## Provider thật, trong chính request ghi

**6 Google HTTP requests =3 countTokens +3 generateContent**, tất cả LIVE_SUCCESS/HTTP200. Một business request mới; không retry Google/Native CREATE. Transport runtime là SDK thật tới Google, không MockTransport/test hook. Receipt20→26; AI runs13→14. Generation2 sinh intent create_work_package với subject test, type10, parent50, assignee23. Native source marker do host gắn; Gemini không cấp quyền và không tự chọn actor.

| Generation | Prompt tokens | Candidates | Thoughts | Total | Output cap |
| 1 | 1513 | 29 | 274 | 1816 | 1500 |
| 2 | 3078 | 40 | 68 | 3186 | 1500 |
| 3 | 3265 | 25 | 188 | 3478 | 1500 |

Tổng provider usage: prompt7856, candidates94, thoughts530, total8480. Thoughts+candidates từng generation303/108/213 đều dưới1500. Worker97.865s <180s. Generation3 chỉ tìm kiếm sau unknown write; yêu cầu phase tiếp theo bị chặn trước HTTP7. Không coi đó là Google429/503: đây là local per-run budget exhaustion.

Quota ledger tăng **7 reservations** trong khi actual HTTP chỉ6: vòng tiếp theo giữ chỗ local trước khi hard budget từ chối gửi. Không diễn giải reservation như request thật hoặc quota Google còn lại. Dashboard lịch sử13successful generations/35474tokens gồm10generation/26994tokens trước đợt này; riêng đợt này chỉ3/8480. Free safety limits13RPM/225000TPM/450RPD, owner quota15/250000/500 giữ nguyên. Không đọc historical peak thành live usage.

## Chuỗi chứng cứ và audit

1. Owner request SHA256 và exact prompt hash trong `armed.json`; UUIDe3626ae0… bindactor19/project5/scope50/exact fields.
2. Core session/CSRF → HMAC/nonce bridge → Gateway fresh Native identity/role. Request gửi từ UI PM thật; không client-supplied actor.
3. Durable claim `owner-run-e3626ae0…` lưu run ID, ngăn gọi lại/replay; create command `owner-create-e3626ae0…`, auto_execute=true theo direct routine policy.
4. `live-run.json` giữ tool intent và lỗi Native503 do timeout30s; Native thật trả201/55.766s. Source marker chính UUID đó trên #367 +author19 liên kết outcome, không dựa vào subject một mình.
5. Explicit operator recovery qua **Core signed bridge**, Native GET-only, exact fields. Reconcile audit `4c8182f9-423c-49de-b090-5ebe37280404`; command correlation `5142b86d-2a03-4a00-b118-5c78f548c268`. Đây là recovery đã phân biệt với hành động browser/model, không phải lần CREATE mới.
6. `provider-audit.json` giữ claims, create receipt, audit và six provider receipts; `reconciliation.json`/UI thể hiện native_reconciled=true, provider_report_completed=false. Worker lịch sử failed_or_unknown không bị ghi lại thành success.

Không có proposal mới; Owner approval +PM checkboxWRITE/scope50 là đường Direct Routine Write thật. Proposal cũ expired chưa apply. Business Tool Worker thực hiện ghi; không nói Supervisor/BA/QA/Reviewer trực tiếp mutation. Stored local Supervisor23353d1f… vẫn có BA/QA/Reviewer outputs, model_used=false; đây là stored-data/deterministic regression, không phải generation mới.

## Security và runtime

Gateway hiện tại: `sha256:4322e8d3154b165e2e6dd98c41428eec0b4a230344c7d022a73efae201a6aa7d`. Core: `sha256:5abec112e69971c9d9a58964fccf717a324a75b96b0d9f83fa7861f66eb7e449`.

Request Live phát sinh trên image5cbf4ab7…; current4322e8d3… đã phục hồi receipt/UI bằng Native read và testclone, không có lượt Gemini mới trên imagecurrent. PM-only-write/nativeRBAC/sessionbinding/CSRF/HMAC/nonce/idempotency/Native form/source+author proof giữ nguyên. Bản recovery chỉ phục vụ receipt đúng actor và revalidate Native visibility; test revoked visibility failclosed. Không cấp operator/shell tools cho Gemini. Private envelope đã consumed/archive và không rearm.

Mọi secret giữ trong private runtime/backup, không có key/password/TOTP/cookie/session trong hồ sơ. Secret scan đối chiếu giá trị secret thật được thực hiện khi chốt; kết quả trong `secret-scan.json`. Không ghi secret vào lệnh, báo cáo hay screenshots. `final-verification.json` xác nhận18serving,17container ngoàiGateway giữID/image/starttime, protectedconfig giữhash, pendingrequests0/busy0, QA23readback và dữliệuMain như đã mô tả. Staging/QuickTunnel/n8n không bị thay hoặc restart.

Assignee identity: prompt giữ nguyên tên tham chiếu `qa-tester` do Owner cung cấp, nhưng function intent/host policy/Native result đều bind User ID23. DB thực tế xác minh login `qa`; không có rename hoặc credential/RBAC change.
