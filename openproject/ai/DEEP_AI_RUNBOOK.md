# Deep AI — candidate, chưa rollout live

**Resume14/10:** active target main8088 (user corrected staging choice). Main unchanged; current stage18091/18092 uses pair262c30a1…/10496cd8… with AI sidebar/native permissions, POST→GET/polling and human proposal preview links.25nativeUI/bridge +97offline tests PASS; real Gemini3.5Lite metadata run25249758… cited329native count, REST/MCP/replay PASS. Proof expiry19:27:19+07 retained, not renewed; enable flag does not guarantee continuous eligibility. Production activation/ledger handoff/approved cutover remain pending. Start existing exact stage pair with `Manage-OpenProjectAI.ps1 -Action StartStage`; never Setup/Stage/seeder/default-image recreate. Full qualificationb78f9fca… RUNNING; CHECKPOINT records terminal result.

**Hiện hành14/10 16:25+07:** provider model `gemini-3.5-flash-lite` đã PASS directGoogle + actual REST/MCP HTTP/stdio/replay và ON_SMOKE_ONLY đến17:21:52+07; runfdd77e23-82fe-4a50-92c2-eb76758b2c8d, QLDAPM_OK. New stage corec77dbdae…/gatewayec4b0e1e…,92units/native329/source hashes PASS; live unchanged. Exact model quota15/250000/500 → local10/175000/350, usage6→10 retained. Scope fixed synthetic only, no arbitrary project chat; no fresh browser/human/live/full-release acceptance. For safe restart use existing containers or exact current pair/3stage overlays; .env/image-lock defaults are historical. CHECKPOINT and gemini-35-real-probe-20261014-1625.json supersede older model/runtime statements below.

Workspace authoritative: `D:/AI project/QLDAPM chat`. Live vẫn official17.9.1 và gateway role-change; candidate riêng có AI Assistant, Insights, 23 REST/MCP tools, proposal xác nhận và receipt. Jira độc lập, không thay credential/bot/lịch.

UI13/10 bugfix: final core0ab293ea…/forkc715001d…, gateway1cd1687b… ở8091/8092. Core500 do controller `ArgumentError` trỏI18n đã sửa;22nativeUI/bridge fixture regressions PASS, đưa vào deep staging/qualification. Form không hỗ trợ chat tự do: Free chỉ fixed smoke; manual Tool mặc định `identity`/`{}`. UI lỗi Gemini OFF hiện giải thích expired verification, không yêu cầu paste key vào chat. Chỉ restart staging bằng pinned pair/Compose stage overlays, không chạy Setup, seeder hoặc đổi live image-lock. User tự BE/TOTP login; browser identity/JSON/provider-denial/create-update-confirm-readback/self-approval-denial/Insights privacy PASS, fixture383 đã dọn. Không agent reset password/2FA/TTL; không independent reviewer/deploy approval. Gemini hiện OFF sau expiry13:26:11, counter4/14 không reset; checkpoint ghi phạm vi test thực và screenshot receipt.

## Credential và điều kiện bật Gemini

**Yêu cầu hiện hành FREE ONLY/staging:** theo `GEMINI_FREE_TIER.md`. Enrollment provider production cũ đã khóa fail-closed; phần lịch sử phía dưới không còn là lệnh được phép để bật provider. Free mode chỉ fixed synthetic probe, không gửi dữ liệu nhân sự/project. Chỉ bật staging sau exact project/free/no-billing/terms/quota verification và smoke thật; không paid fallback.

Key cũ trong chat đã được người dùng thu hồi; replacement hiện có giữ nguyên. Ngày13/10 đã đọc đúng account/project trong official UI: Free Tier, No billing account/not linked, quota5RPM/250000inputTPM/20RPD. Assistant ghi documentary observations và chạy helper theo explicit user authorization; không independent human review hoặc automatic billing API check. Direct Google smoke và REST/MCP HTTP/stdio integration PASS thật, tổng2probes/4reservations, Linux4/14/circuit false. Staging **ON_SMOKE_ONLY** đến13/10/2026 13:26:11 Asia/Bangkok, sau đó fail-closed; không gửi dữ liệu công việc/nhân sự, không paid fallback. Live không bật provider/cutover. Codex/MCP và báo cáo local không cần Gemini.

Trước khi enrollment: operator phải có bằng chứng cho project API/model `gemini-3.8-flash`, điều khoản cho phép dữ liệu cần gửi và cơ chế phía provider ngăn overage ngoài quyền lợi được duyệt. Credit/budget alert/local token counter không đủ. Nếu không bảo đảm được, giữ provider OFF và dùng local/MCP. UI phải thông báo dữ liệu cho thành viên trước khi gửi dữ liệu nhân sự lên provider.

Chỉ sau khi các điều kiện trên được xác minh, nhập key ẩn tại local:

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat\openproject\ai'
& '.\.venv\Scripts\python.exe' free_tier_staging.py enroll # staging only, stays OFF
# Dừng provider ngay, không xóa dữ liệu:
& '.\.venv\Scripts\python.exe' manage_deep_ai.py disable-provider
```

Lệnh dùng operator attestation/documentary reference, không tự kiểm chứng Google billing hoặc quyền lợi bằng API. Không gửi key vào chat, browser, Compose environment hoặc sandbox. Runtime phải giữ ACL LUIM/SYSTEM từ Setup; không dùng thư mục public/shared cho credential.

## Proposal và danh tính

PM19/BA20 là role live hiện hành; BE21/FE22/QA23 không đổi. Mỗi người hoàn tất password/TOTP và Register token của chính mình. Chưa nghiệm thu ba credential BE/FE/QA thật.

Mọi ghi qua candidate REST/MCP/UI tạo proposal gắn actor, preview, phiên bản và SHA256; TTL15 phút, thực thi một lần. Reviewer độc lập và native hard gate vẫn áp dụng sau xác nhận; người xác nhận proposal không thay thế reviewer hoặc operator deploy.

```powershell
& '.\.venv\Scripts\python.exe' manage_deep_ai.py confirm --user-id 21 --proposal '<uuid>'
```

Lệnh chỉ dùng Bearer local và token cá nhân. Timeout: kiểm tra proposal/request receipt; trạng thái `failed_or_unknown` không được tự retry với key khác. Update/transition receipt là transaction PostgreSQL, actor-scoped, gắn journal; signature riêng nhận diện gateway delegation, lịch sử cũ ghi unknown.

Create timeout chưa có actor-bound native receipt: giữ UNKNOWN và operator đối soát, không coi ticket cùng Source ID là bằng chứng AI đã tạo. Create mới với Source ID đã tồn tại trả409. Hai code confirmation cùng hash base được serialize; confirmation thứ hai trả stale, không ghi đè bản mới.

## Test evidence

`request_test` nhận `suite`, `workspace_actor` và tùy chọn `work_package_id`. Job gắn ticket chụp gate revision lúc yêu cầu, snapshot code bất biến khi chạy; result.attestation do broker ký riêng, chứa project/ticket/revision/snapshot/output hash. Chỉ ghi `verification: automatic` với đúng receipt và snapshot; sửa scope/revision hoặc giả chữ ký bị từ chối. Job không gắn ticket chỉ là test receipt thông thường, không automatic gate evidence.

Chỉ `gate-policy`/`core-integration` được gắn ticket. `gateway` kiểm tra image hạ tầng đã pin, không kiểm tra code của workspace, nên Service/broker/core từ chối dùng kết quả đó làm automatic evidence. Native receipt acceptance trong `tests.sandbox` dùng key/danh tính staging giả, transaction rollback; không mở SQLite live hoặc đưa credential production vào runner.

Manual evidence được ghi `verification: manual`; không chứng minh test đã chạy. Automatic smoke suite chưa có và bị từ chối; smoke/deployment Test vẫn cần xác nhận thủ công đúng quyền. Các suite kiểm tra core/gateway không chứng minh 53 User Story đã thành sản phẩm.

## UI, báo cáo và lịch

Candidate thêm menu AI Assistant/Insights vào project private, dùng session/login/CSRF native. Core→gateway là địa chỉ private cố định và assertion HMAC actor/project/nonce/TTL30s; gateway xác minh lại membership/token. Không có endpoint Internet cấp token hoặc tự confirm/deploy.

Insights tính local, snapshot PostgreSQL; PM xem cả project, người khác chỉ self và thêm giải trình. Cửa sổ7/30/90 ngày, kỳ trước để so sánh process actions, Sprint có ngày thật và active/completed. Cycle/handoff dùng lịch sử assignee, dừng attribution khi reassigned; test first-recorded không che failure ở kỳ trước. Nguồn/sample/coverage đi cùng số liệu; thiếu baseline commitment/blocker/time-entry/verified-bug thì chưa đủ dữ liệu, không suy thành điểm năng lực. Không ranking hoặc quyết định nhân sự.

GoodJob cron23:55 Asia/Bangkok chỉ tạo snapshot local, không gọi Gemini. Actor/assignee và manual/automatic/unknown được phân biệt; role hiện tại không áp ngược lịch sử.

Free mode chỉ cho đúng fixed synthetic smoke prompt; kiểm tra shared service trước create run/idempotency và tại adapter trước outbound, không dựa keyword scrubber. Nhánh general-tool chưa bật: fixture JSON claims validator buộc tool index/path/type/scalar khớp result thật, source hash và không prose/ranking. Đây là xác minh trích dẫn sự kiện, không chứng minh chất lượng hoặc năng lực nhân sự. Fixed private subprocess đặt deadline120s cho toàn model/tool; timeout dừng worker, giữ failed_or_unknown và đối soát native/proposal/job receipts, không tự retry. Job sandbox đã queue có thể tiếp tục độc lập. Provider vẫn OFF cho dữ liệu nhân sự/Free arbitrary prompts; chưa nghiệm thu Google general-tool contract thực.

## Rollout còn phải hoàn tất

Qualificationc23cabff… đã PASS28checks gồm actual paired Docker success/failure rollback và remote HTTP/stdio MCP; signature/candidate13/10 đã xác minh nhưng proof24h hết hạn. Không tự gia hạn hoặc dùng proof này deploy. Rehearsal586050dd… giữ schema candidate sẵn có; chưa kiểm chứng official-to-candidate binary upgrade, real TOTP/Codex hoặc live glue. Restore33tables/database/assets/config/hash PASS; giữ volume/backup, test containers/networks đã dọn. Đầu checkpoint là nguồn trạng thái hiện hành; các đoạn resume phía dưới là lịch sử.

Resume23:32: source comparison đã tái hiện RED từ full backup thực, sửa `backup_state.rb` giữ full hash cho restore và source hash riêng cho migration; các bảng AI đã tồn tại vẫn phải bất biến, chỉ bảng AI mới rỗng được phép thêm. Old full-backup restore vẫn so rows/SHA, không dùng metadata source mới để đánh trượt backup cũ. Rehearsal clone dọn container/network UUID sau dùng, giữ volumes/backups. Main SDK test cấp Bearer24h mới bằng synthetic native credential mỗi lượt; không tự Register người thật. Qualification18363824… đang chạy, chưa sealed; xem checkpoint trước thao tác.

1. Tạo keys riêng bằng `manage_deep_ai.py prepare-ui` tại private runtime: gateway/ui.key và operator/test-receipt.key. Core chỉ mount hai file readonly; tuyệt đối không mount operator directory/approval.key. Gateway không đọc test receipt signing key.
2. Promotion đồng bộ core/gateway đã có implementation: release nhận hai immutable digests, đóng hai tunnel, freeze gateway trước snapshot SQLite/credential/config, pin cả hai image và giữ Gemini OFF. Tạo private `openproject/ui-bridge.yml` bằng hai mount file readonly, không mount operator directory; keys trùng nhau bị từ chối. Manager/release tự dùng override, temporary restore stack không dùng key live. Rollback chọn image/volume/config trước, giữ state lỗi riêng và gateway dừng/maintenance. Fixture đã chạy; chưa diễn tập glue trên stack Docker độc lập.
3. Qualification mới khóa commit/hai image/harness, migration, receipt, UI privacy, 23tools, restore33tables; proof chỉ core cũ bị từ chối. Các suite transport/sandbox dùng cùng image pair đã chọn, không fallback tag mutable hoặc image-lock staging cũ. Human release approval thêm deployment hash (.env/image-lock/config/credential/keys/volume/bridge); thay file sau duyệt phải duyệt lại. Candidate chưa pin vào live .env; không chạy Setup để ghi đè runtime hoặc hạ staging.
4. Diễn tập chính glue release/rollback trên stack giả trước khi người vận hành duyệt exact live commit/digest/migration/backup/test. Chỉ operator phê duyệt local, AI không tự Approve. Giữ volume cũ và provider OFF đến khi đủ điều kiện.
5. Nghiệm thu công việc kiểm chứng riêng trên live, năm danh tính và Codex host/TOTP/WebSocket thật. Báo cáo staging/SDK không thay thế các bước này.

Kiểm thử thực và image/commit hiện hành ở `CHECKPOINT.md`/`TEST_MATRIX.md`. Local54unit PASS, metrics/receipt fixture, UI/bridge/privacy, API5role giả, write/replay và concurrency closed-parent đã có bằng chứng. HTTPS SDK23tools là kết quả lịch sử trên gateway cũ, chưa nghiệm thu lại pair mới. Restore core cuối33tables/assets/config và sandbox với signed job attestation → native gate PASS. Full broker queue lifecycle, cutover glue Docker, Gemini hiện hành và toàn bộ concurrency/security/resource matrix chưa nghiệm thu; không coi candidate là production hoàn tất.

Resume11/10: sandbox3suite và signed workspace receipt→native automatic evidence đã PASS trên runtime giả độc lập (transaction rollback). Chưa full broker queue/identity lifecycle trên main gateway hoặc resource-exhaustion attack matrix.

Restore core candidate cuối0f8f5a1c… PASS33tables/assets/config, evidence private17ccb077…; đây không phải glue coupled release. Nếu lỗi khi đã bắt đầu mở truy cập sau cutover, giữ pair/state mới và fence truy cập, operator đối soát trước rollback có phê duyệt; không tự chọn DB/SQLite cũ làm mất ghi mới.

Lịch sử số test phía trên không phải kết quả lượt mới. Xem đầu checkpoint: gateway216b1920… và core0f8f5a1c… đang chạy staging; 65Windows unit PASS, final Docker65discovered/2skip PASS; main SDK HTTP/stdio và signed native bridge PASS. Qualification mới đang chạy, chưa sealed. Broker/token/proposal CLI dùng Linux fixed stdin protocol; không public SQL/shell/approval route mới. Production chưa promote bản sửa; CLI source mới cần paired candidate, không restart live broker bằng source mới trước approval.

Sau Stop, Resolve dùng explicit offline Linux one-shot/pinned/no-network/no-pull, không bật gateway hoặc thực thi job. Running job thiếu signed operator result receipt không được acknowledge. Receipt luôn yêu cầu đối soát queue; lỗi sau job không auto retry, không xóa/reset SQLite/WAL/SHM. Free helper/role-change/setup/stage preparation từ chối mở host SQLite nếu gateway tương ứng chưa stopped. Đây là fix/test single-OS trên dữ liệu giả, không thay thế Docker coupled release/rollback hoặc live acceptance.
