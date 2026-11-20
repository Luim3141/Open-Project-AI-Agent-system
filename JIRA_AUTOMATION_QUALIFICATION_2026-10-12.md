# A02–A05 qualification — actor sửa, QA companion staged, chưa enable

## Scope và route

Site luimjiraqldapm.atlassian.net / cloud560ef0cc-d24b-4613-98d3-d541afe8f32b / QAG3/10002. Official atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue QAG3-332 PASS; discover hai truy vấn vẫn không có sửa actor/automation. UI fallback đã báo trước. Supplemental inspect_automation readComplete=true; cố định API expression/validation qua code admin hiện có và credential DPAPI ngoài repository, không in secret. Forge CLI vendor pin14.1.0, deploy Node24 bundled.

## Đã làm thật

- A03 UUID01a12ee4-1276-76b4-ba01-49bdeda52f9d và A04 UUID01a13075-71e9-7e0f-b65f-006ec2a4b83b: actor AutomationforJira → **User who triggered the event**, Save trên Jira. Không cấp role/scope/admin hoặc ủy quyền PM tĩnh. Summary API actorAccountId=null vì actor động; UI A04 reload xác nhận mode thật, không suy null thành mất actor. A04 description cập nhật đúng mode. Gate PM cũ vẫn có thể từ chối non-PM; UI cảnh báo special-admin/Marketplace actor có thể fallback AutomationforJira. Chưa test execution.
- App development **2.14.0** deploy exit0. Chỉ thêm module qag3-qa-freshness, **10 module cũ deep-equal giữ nguyên**; không API scopes/function/storage/egress/billing. SHA256 manifest8cb2db63bf30232fc053aa7a8a4507ba8ab0f6532ab29e6faacb96963bbabda9. Catalog đã có module mới qua preview native. Chưa gắn module vào workflow; QA-current cũ vẫn có lỗi cost.
- Companion dùng getNewestChangelog cho PASS IN TESTING→REVIEW, status mới nhất và5field summary/description/parent/assignee/evidence; không dùng changelogs toàn bộ. Jira read-only QAG3-332 trả true, typeBoolean valid. Đây là phần freshness, **không thay authenticated QA provenance/checklist/pending field gate** và không được dùng một mình. API có chi phí bounded theo field, không chứng minh full E2E/concurrency.
- Supplemental code thêm fixed preview_task_qa_freshness cho **chỉ Task QAG3 Approve13/Deploy14**, yêu cầu qag3-qa-current hiện có vẫn enabled, giữ mọi điều kiện/rule/layout/action/screen. Route riêng thêm gate cho workflow active; không gỡ guard inactive của các route cũ. Exacthash/900s/current-version/lock/no-replay/readback của apply_change giữ nguyên; không tool enable automation mới.

## Preview thật, chưa apply

- PreviewID fbbcc261-a1bc-4400-bc8a-e2ebe1fa2f3a.
- Fingerprint **7801068db638d6baee13ee83e5e70107ee488697e46f5f5e6569e171a741ef74**.
- Jira workflow validation errors=[]; blockers=[]. Diff chỉ thêm qag3-qa-freshness vào13/14. Actor/scope của rules không nằm trong lô workflow này.
- Preview tạo qua supplemental CLI tools/preview_qa_freshness.py, không phải invocation registered official MCP. Audit đầy đủ ở LOCALAPPDATA/QLDAPM/jira-admin-audit/<previewID>.preview.json.
- Đã yêu cầu chủ dự án duyệt đúng fingerprint trước apply. Hết15phút phải đối soát/tạo preview mới và xử lý approval theo guard; không tự giả lời duyệt. Chưa gọi apply_change hoặc POST workflows/update.
- Rollback chỉ hai gate mới theo current-version preview riêng; chưa được phép bỏ QA-current hoặc uninstall app đang dùng. Baseline code tại forge/qag3-validator/manifest.before-qa-split-2026-10-12.yml.

## Kiểm thử và lỗi còn thật

Node predicate fixtures PASS; freshness fixture PASS (stale field/rework/empty/1000 irrelevant history/cross-project,10 old modules unchanged). 105Python Jira regression/stdio PASS +1new additive/idempotence/partner-required test PASS. Forge lint PASS; deploy source node24, lint đầu dùngnode25 có warning, không dùng nó cho deploy.

Combined newest-change prototype Boolean type valid nhưng **forced-all-read-paths vẫn400 expensiveoperations>10**. Không coi Boolean=false sớm là đã sửa lỗi. tools/diagnose_qa_newest.py giữ experiment này; module qag3-qa-current trong app2.14.0 chưa tối ưu. Chỉ sau companion gắn/enabled đọc lại mới được tách phần provenance khỏi QA-current, verify positive/negative và deploy giữ conjunction, tránh cửa sổ thiếu freshness.

QAG3-332 vẫn REVIEW; evidence fixture cũ có literal newline escapes, cần retest/attest mới đúng cấu trúc ở lượt E2E, không sửa rồi coi là chữ ký QA cũ vẫn valid. Không chuyển issue trong lượt này. A02 chưa đủ thử finalTaskDone; A03/A04 cần thử quyền và đổi Parent; A05 chưa chỉnh routing/coordinator hoặc mail/quota/concurrency. Labels marker không atomic, không hứa exactly-once. Không bật bất kỳ A02–A05 nào; A01 giữENABLED, monitorPAUSED;329WBS/timeline/baEpicDone/KAN/SAM1/OpenProject giữ nguyên.

MCP process qag3-admin hiện đang nạp source cũ: inspect_expression_validation báo EXPRESSION_MANIFEST_CHANGED cho manifest mới. Không nới guard hoặc restart app mù; validation/preview của nguồn mới đã chạy qua fresh supplemental CLI, stdio fresh catalog22tools PASS. Tool mới cần reload connection trước registered invocation, không nói hiện đã callable trong server cũ.

UI hiện có link Standard trial; chưa kiểm tra billing/plan/quota thực, không tự đổi gói hoặc bậttrial. Banner không phải chứng cứ đã chuyển Free/billing0; cần đọc quota thực trước A05 gửi thật.

## Tiếp tục

Sau exact-hash approval: apply additive companion và đọc lại hai gate; tối ưu QA provenance trong conjunction, negative stale tests; test A02–A04 trên fixtures tách WBS; hoàn thiện reviewer/routing/notification dedup A05 và quota thật. Bật từng rule sau qualification, không bấm Enable cả4 để che blocker. Screenshot actor A04: jira-bot/QAG3-A04-trigger-actor-2026-10-12.jpg.

Primary source: [Jira expression types/getNewestChangelog](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/), [giới hạn expression](https://developer.atlassian.com/cloud/jira/platform/jira-expressions/). Companion thật type/runtimeread PASS; không suy local test hoặc config thành Jira E2E PASS.
