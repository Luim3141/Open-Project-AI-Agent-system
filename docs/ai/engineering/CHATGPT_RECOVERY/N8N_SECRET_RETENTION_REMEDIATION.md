# Trạng thái sau Owner approval — MAIN đã đổi

Proposal30218aff đã được duyệt và áp dụng. Xem [MAIN_ROLLOUT_RESULT.md](MAIN_ROLLOUT_RESULT.md) và `rollout-20261101T110426Z/deployment-result.json`. Các đoạn NOT_DEPLOYED/AWAITING_OWNER_APPROVAL phía dưới là pre-rollout snapshot, không phải trạng thái hiện tại. Chưa human acceptance/full business E2E.

---

# n8n secret retention — candidate đã kiểm thử

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

P0 confirmed trên MAIN:13interactive workflows từng giữ Authorization và webhook token trong execution_data. Không có bằng chứng truy cập trái phép; không xuất raw headers/DB vào repo.

Clone baseline cho thấy saveDataSuccessExecution=none/saveDataErrorExecution=none/manual=false/progress=false **vẫn chưa đủ** để bảo đảm execution storage không có canary (n8n-retention-before-redaction.json). Sửa tối thiểu tại central execution-persistence.writeData và legacy ExecutionRepository update path. Upstream file SHA guard và unique markers làm build fail closed khi version thay đổi. Không sửa executing input: authentication/working workflow vẫn nhận giá trị gốc; chỉ persisted copy được redact.

Redactor bao gồm header object keys, n8n headerParameters name/value pairs, Authorization Basic/Bearer trong strings và signature/cookie/API-key headers. Giữ cyclic flatted structure và nonsecret status/correlation. Payload malformed fail closed. Independent review tìm header-pair gap; RED→GREEN đã lưu, không chỉ test Bearer object.

Candidate `sha256:9e8d3393ca28a6603f3890218aeb3bb280952262c134e230b033380a2fd54e32`. Clone actual Gateway→WF04 ACK và canary HTTP success200/error500/CLI execute exit0. Execution_data4rows cùng các execution tables/daemon log được scan: không canary. Disabled HTTP header fixture trong workflowData và Basic error/manual paths được bao phủ. CLI output được redact trước ghi log. Workflow definitions gốc chứa synthetic fixture được giữ private; không dùng synthetic secrets cho serving.

Giới hạn: manual đã thử qua CLI execute, **editor/manual UI: PENDING OWNER MANUAL UAT**. Không coi đây là chứng minh mọi arbitrary source string hoặc một upstream storage backend khác đều được redact. Image pin2.43.6; upgrade phải rebuild/verify hooks/canary. Nguồn chính thức tham khảo: [execution settings](https://docs.n8n.io/hosting/configuration/environment-variables/executions/) và [CLI](https://docs.n8n.io/hosting/cli-commands/); bằng chứng hành vi là clone version cụ thể.

Rollout đề nghị thay image n8n giữ nguyên owner/encryption/env/volume/ports, targeted WF04 retention; không bulk import16workflows. Raw historical executions chưa được xử lý. Sau backup n8n cold-consistent và exact owner approval riêng: inventory bằng fingerprint/boolean, xác định bearer/webhook credentials còn hiệu lực, chuẩn bị replacements private, đổi đúng consumers, test scoped auth, revoke old credentials, rồi purge chỉ affected execution IDs theo retention plan được duyệt. Không rotate Gemini/TOTP/DB hoặc toàn bộ user keys theo suy đoán; không xóa history tự động trong batch này. Backup cũng chứa dữ liệu nhạy cảm nên phải giữ private/access-limited.
