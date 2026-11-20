# QAG3 — MCP local hỗ trợ switch scheme, chưa migration

## 1. Kết quả hiện hành

Đã bổ sung đường **populated-project switch** vào MCP supplementary `qag3-admin` đã đăng ký, không thay global config hoặc credential. Đây là tích hợp local gọi API Atlassian chính thức, không phải thao tác admin của official Rovo MCP.

Hai tool mới:

- `preview_scheme_switch()`: cố định QAG3/10002, nguồn10003 → đích10004, không nhận URL/project/scheme/mapping tùy ý. Đọc snapshot, workflow, calculator mapping và lưu audit local; không ghi Jira.
- `inspect_scheme_switch_result(preview_id)`: chỉ poll task có trong audit của operation switch; COMPLETE phải đối soát association10004, mapping3workflow và snapshot329 trước khi verified.

Ghi migration vẫn qua `apply_change(preview_id, approved_fingerprint)` hiện có: exact human approval, hạn900s, kiểm tra stale, rollout evidence T01–T23, lock, audit trước ghi, một lần POST và không retry mù. Không sửa `empty_project()` hoặc làm project rỗng; tool `preview_scheme`/assign cũ giữ nguyên.

## 2. Đã xác minh thật trên site

Site: https://luimjiraqldapm.atlassian.net; cloudId560ef0cc-d24b-4613-98d3-d541afe8f32b; QAG3/10002/classic. Official `atlassianUserInfo`, `getAccessibleAtlassianResources`, `getJiraIssue(QAG3-2)` PASS đúng owner/project. `discover` không expose switch scheme.

Qua `tools/jira_mcp.py --server qag3-admin` / Codex app-server, schema `preview_scheme_switch` được advertised và actual call thành công. Supplemental preflight: ADMINISTER=true; ADMINISTER_PROJECTS=false; chưa thử admin write.

Preview đầu22c50c29-3657-4c7a-9b33-d7c5c2041a9a chứng minh snapshot/calculator khả dụng. Sau sửa chuẩn hóa thứ tự danh sách không mang ý nghĩa, preview hiện hành:

- ID: `0794ba52-fc67-4baf-b3f7-ff9bdf19bcfb`.
- SHA256: `dc16f48378b094ccb9ec2acf69f48fdfc9e37a089c9d6855b61dd8944997a936`.
- createdAtEpoch1791730173.0107896; hiệu lực900s, **không được coi là đã duyệt**.
- readComplete=true;11Epic/53Task/265Subtask=329;316Done10009/13InProgress3,0ToDo.
- Epicv7/Taskv6/Subtaskv6; scheme hiện hành10003, đích10004.
- Response calculator trả10008 cần mapping cho10000/10011/10010. Payload có10008→10010 ở cả3type; đây là mapping cấu hình cho trạng thái hiện có0issue, không đưa316Done hoặc13InProgress vềNEW.
- Parent trả318Task/Subtask;description/duedate/timespent/assignee/resolution trả đủ329 ở snapshot. Parent của Epic bị bỏ khỏi response, giữ là missing/UNKNOWN, không gánnull.

`POST /workflowscheme/update/mappings` chỉ tính toán mapping. Cách dùng source scheme10003 và desired workflows của10004 đã trả kết quả thật trên site, không sửa source scheme. `POST /workflowscheme/project/switch` **chưa gọi**, khả năng ghi switch/303 task vẫn NOT VERIFIED.

## 3. Điểm chặn chính xác

Preview trả: **Jira T01-T23 gate tests and PM review not recorded; activation blocked**. `rollout-evidence.json` chưa có. Không ghi kết quả giả định của WBS/worklog/điểm thành Jira gate PASS, không tạo proof hoặc approval hash giả.

Không gọiapply_change, không bắt đầu switch/publish/migration. Independent `inspect_scheme` sau preview vẫn10003. Chưa kích hoạt3workflow, chưa bậtA01–A05, không resume monitorPAUSED, không UI fallback, không KAN/SAM1/OpenProject/billing mutation.

Phần thiếu không còn là API chỉ hỗ trợ project rỗng. Cần một lượt qualification được phép cho các workflow/gates đang inactive để thu Jira E2E thực trước rollout; thiết kế hiện hành vẫn có phụ thuộc E2E-before-activation. Tool mới **không tự mở ngoại lệ** cho test rollout, không tự tạo project thử, gắn workflow cho issue type thử hoặc cấp quyền mới. Sau qualification/PM review cần tạo preview mới và duyệt đúng hash, không tái dùng preview hết hạn này.

## 4. Kiểm thử và bảo toàn

105 Python Jira regression/transport/unit tests PASS; trong đó11test mới về snapshot đủ trang, scope329, duplicate/foreign/status/Parent mismatch, unknown/null, mapping, gate blocker, stale preview, one-shot async POST, failed/unknown task, preserved readback và list order. Stdio SDK thật xác minhcatalog21tools và missing credential fail-closed. Mock PASS không phải Jira E2E.

Before snapshot gồm key/id/type/status/parent/assignee/labels/Resolution/description/duedate/timespent/updated; missing fields không đổi thànhnull. Snapshot và workflow/calculator nằm trong fingerprint; apply đọc lại, có thay đổi phải preview mới. Readback cho phépupdated đổi do migration, không cho Resolution/trạng thái/Parent/assignee/description/giờ thay đổi. Chưa đọc lại chi tiết từng worklog sau migration vì chưa có migration; poll ghi `worklogDetailsVerified=false`.

HTTP không follow redirect.303 chỉ nhận task Location đúng cloud gateway; task đọc lại bằngGET, không POST lầnhai. FAILED/CANCELLED/DEAD/UNKNOWN không được verified. Bảnbefore/audit giữ tại `%LOCALAPPDATA%/QLDAPM/jira-admin-audit`; không chứa token. Không ghi đè collector/runtime/Sprint baseline.

## 5. Rollback và giới hạn

Nguồn code trước change có thể khôi phục bằng diff bỏ2tool/nhánhswitch/allowlist mới và test liên quan; không ảnh hưởng sourceForge/gates hoặc dữ liệuJira vì chưa ghi. Sau migration, reverse switch phải có preview/approval/mapping riêng, không tự xóa/move/reimport issue. Đường reverse chưa implement/live-test; chưa hứa automatic rollback.

Snapshot nhiều request không nguyên tử; fingerprint và admin lock không khóa người khác đang sửaJira. API switch được Atlassian đánh dấuExperimental. Cần independent readback sau actual switch; migration vàoDone không phải nghiệm thu sản phẩm.

## 6. Nguồn và mã

- [Official switch/calculator API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-schemes/).
- [Official empty-project assign API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-scheme-project-associations/).
- Research/OpenAPI exact schemas: `JIRA_SCHEME_SWITCH_API_RESEARCH_2026-10-11.md`.
- Implementation: `tools/jira_admin_mcp.py`; tests: `tests/test_jira_scheme_switch.py`, `tests/test_jira_admin_stdio.py`.
