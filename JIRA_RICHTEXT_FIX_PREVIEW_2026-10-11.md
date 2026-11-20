# QAG3 — sửa lỗi RichText, candidate chưa deploy

## Kiểm tra engine thật, chỉ đọc — 11/10/2026

Added fixed `inspect_expression_runtime()` trong registered supplementary MCP (source19tools), reuse parser10module/hashpin; chỉ gọi official POST `/expression/evaluate`. Không nhận expression/URL/context/actor từcaller, không ghiissue, khônguserimpersonation. Official identity/resources/QAG3-3smoke PASS trướclượt.

Gọi thật10expressions của source605a58b1… trên QAG3-1Epic/QAG3-2Task/QAG3-3Subtask, originalIssue là cùng committed issue, user luôn tài khoản ownerPM đãauthenticate. Kiểm tra response project/key/type/actor/Boolean đầy đủ; evaluationComplete=true, PM-only=true và9gate khác=false trênbacklogchưa nghiệmthu. Khôngengineexception trong10request.94Pythonregression/stdio PASS; scope/actor/malformedresponse tests giữfailclosed.

Đây là committed-data evaluation, **không** pendingtransitionfields, khôngQAactorpositive, khôngworkflowcondition/screen/postfunction/migration/concurrencyE2E. Explicit jiraE2EVerified=false/pendingTransitionFieldsTested=false. Không ghi rollout-evidence.json; file này vẫn chưa tồn tại. Không dùng10runtimeevaluation hoặc94localtests để lấp23E2EPASS. KhôngForge redeploy/activation/migration/automationenable/monitorresume ởlượt này.

Yêu cầu user bỏquytrình không cho phép tựsửa safety/approval guard hoặcfakeQA/evidence. Gate rollout còn đòi kiểmthửthật; supplementary association vẫn chỉprojectrỗng nên không hỗtrợ329migration. ĐườngUI đãquan sát làSwitchScheme, nhưng khôngdùng nó đểné activationcheck. Cần đườngqualification có giới hạn/đúngactor và hardgate trướcmassmigration; chưagiảđãđạt. Thamchiếu officialexpressionengine https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-jira-expressions/.

## Hiện hành: development2.5.0 đã deploy — 11/10/2026

Sau preview hash605a58b1… ở lượt trước, chủ dự án yêu cầu rõ “cứ deploy và triển khai hết”. Đã thực hiện Forge CLI pinned14.1.0 `deploy --environment development --non-interactive` trên đúng app hiện có: lint No issues found, exit0, Deployed, version2.5.0. Không đăng ký/cài app mới, production deploy hoặc scope/function/storage/egress/billing thay đổi.

MCP official identity/resources/QAG3-2 PASS. Supplementary `inspect_workflow(task)` đọc lại Taskv6/fe305b00… và catalog đủ10Forge validator; `inspect_scheme` vẫn10003. Forge version list development độc lập trả major2/10modules/0scopes/0functions/0remotes/0services/noLicense/noEgress, không có timestamp minor2.5; không dùng ngày major để gán ngày deploy mới. Jira type-check saudeploy10/10Boolean/allValid=true.93Python regression/stdio rerunPASS. Source tool trả sourceVariant=richtext-fix, không suy deployment từ sourcehash; bằng chứng deploy là CLI success riêng.

Chưa activation/migration329issues, A01–A05enable hoặc Jira transitionE2E/QA thật. Approval deploy bản sửa không phải chữ ký exacthash cho những preview workflow tương lai; guard của tool còn giữ nguyên. FullLead/BA/FixBug/retest và gate-first/testrollout vẫn chưa hoàn tất. Không tạo giả QA/rollout-evidence hoặc đổi monitorPAUSED. Các mục candidate/chờduyệt bên dưới là lịch sử trướcdeploy.

## Bằng chứng mới

Official MCP identity/resources/QAG3-2 xác minh đúng owner, cloudId560ef0cc-d24b-4613-98d3-d541afe8f32b và QAG3. Không browser/issue write trong lượt này.

Supplementary registered MCP `inspect_expression_validation` được nâng từ `check=syntax` sang `check=type` theo enum OpenAPI Atlassian. Cả10expression của baseline đã deploy ba890f52… được gửi tới Jira, response type-check:

- 6 module trả valid=true/Boolean.
- `qag3-qa-current`, `qag3-subtask-acceptance`, `qag3-epic-readiness`, `qag3-epic-acceptance` trả TypeError tại `new RichText(value)`: nhận RichText thay vì Map/ADF.
- Type analysis trả trường expression là biểu thức cuối, bỏ các let declarations. Gateway chỉ chấp nhận exact full echo hoặc exact final expression của source đã pin, đúng10kết quả/đúng thứ tự/boolean valid; response thiếu hoặc khác bị chặn. Không cho expression/context/URL tùy ý.

## Nguyên nhân và sửa tối thiểu

`issue.description` có kiểu RichText và phải đọc `.plainText`; helper `plain` dành cho multiline custom field Map/ADF hoặc String không phù hợp với description. Bản sửa thay đúng5chỗ trong4module: readiness đọc description trực tiếp và các gate so sánh nullable description.plainText. Giữ helper custom field, logic actor/QA/checklist/scope/child-Done, module keys, app/runtime và toàn bộ permissions.

Fixture trước đây dùng description String nên che mất lỗi. Cập nhật fixture đưa description thành object plainText tương ứng RichText: trước sửa tái hiện FAIL tại kiểm tra đổi mô tả phải làm QA stale; sau sửa PASS toàn bộ suite. Đây là regression logic synthetic, không phải Jira transition E2E.

## Candidate và kiểm tra

- File: `forge/qag3-validator/manifest.yml`.
- SHA256: `605a58b13b101191226433def8e44ba950f958a17711220419a09b9eb175b3de`.
- Registered MCP gọi thật Jira type analysis: allValid=true, cả10module type Boolean; manifestKind=candidate-not-deployed, jiraE2EVerified=false.
- Node predicate fixtures PASS sau red→green.
- Forge lint: No issues found.
- 93 Python Jira regression/stdio tests PASS.
- Không deploy/activate/migrate/enable automation, không đổi credential/billing hoặc khởi động monitor. Source khác deployed baseline; không gọi bản sửa là live.

## Preview triển khai và rollback

Đề xuất chỉ deploy development app đã cài, cùng10expression module; không scopes/function/storage/egress mới. Bản sửa ảnh hưởng gate đã tham chiếu app development nhưng workflows vẫn inactive theo checkpoint; phải đọc lại catalog/config trước bước rollout tiếp. Đã gửi yêu cầu duyệt đúng manifest hash, đang chờ trả lời. Không tự tạo approval hoặc chuyển sang production.

Rollback source: thay nullable description.plainText về helper plain tại đúng5chỗ, kiểm tra source fingerprint về baseline ba890f52… và deploy development lại sau preview/approval riêng. Không uninstall app hoặc xóa workflow đang tham chiếu validator. Candidate chỉ sửa lỗi kiểu dữ liệu, chưa hoàn thiện Lead/BA/FixBug hard gate hoặc E2E/migration dependency.

## Nguồn chính thức

- [Jira expression types](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/): Issue.description là RichText, RichText.plainText và constructor Map/ADF.
- [Expression analyse](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-jira-expressions/): syntax và type analysis experimental.
- [OpenAPI đã đọc](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json?_v=1.8516.130): check enum syntax/type/complexity, syntax là mặc định. Type PASS chưa chứng minh quyền visibility, concurrency hoặc transition E2E.
