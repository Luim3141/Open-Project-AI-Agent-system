# Main Gemini Supervisor UAT — preview, chưa gọi Google

Mục đích: kiểm chứng một chuỗi model-driven thật Browser → Rails/HMAC → Gateway → Supervisor model planner → BA → QA → Reviewer local → synthesis → kết quả Web/Monitor. SmokeQLDAPM_OK trước đó chỉ chứng minh provider connectivity.

## Phạm vi một lượt

- Actor Native PM19, project5, đúng phiên Owner đang đăng nhập; engineGemini theo cấu hình đã lưu.
- Prompt cố định:

> BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49. Chỉ trích dẫn dữ liệu được cung cấp, nêu rõ thông tin còn thiếu; không tạo đề xuất ghi.

- ExplicitID49 giới hạn Native context về một WP. Dữ liệu có thể gửi tới Google: prompt, subject≤300chars, description≤1000chars, status/dates/version, tối đa2businesscomments≤250chars mỗi mục, tối đa3knowledgehits chỉ nếu cùngID49 và còn quyền, các kết quả phân tích BA/QA trước đó, metadata project summary/counts/Sprints/options. `safe_text` tiếp tục lọc mẫu thông tin xác thực/PII hiện có; guard không được nới. Không gửi password/TOTP/cookie/APIkey vào payload nghiệp vụ. Google sử dụng key ở backend để authenticate như cấu hình có sẵn.
- Main không có knowledge index được ingest trong UAT này. Không tự ingest tài liệu hoặc mở rộng từ một WP ra329descriptions.
- Read-only/allow_routine_writes=false/write_scope_ids=[]; không tools ghi, proposalconfirm, WPmutation, shell, credential/RBAC/model/billing/config changes.

## Ngân sách đã có trong runtime

Main `multi_agent`: max_model_calls5, max_http_attempts12, max_agents3, max_output_tokens3000/generation, max_context_chars32000, timeout300s, call_timeout90s, retry_limit1. Không thay những giá trị này để test.

Prompt yêu cầu đúngBA+QA: bình thường1planner+2specialistgeneration và3countTokens, tổng6HTTP. Retry có thể xảy ra theo runtime; trầncứng12HTTP/5generateContent, tối đa15000outputtokens nếu chạm5generations. Đây là ngân sách tối đa, không cam kết dùng hết hoặc khôngretry. Reviewer/synthesis code local không gọi model thêm. Không chạy lầnthứhai nếu timeout/unknownoutcome; đọc existingrun/receipts trước.

Model/key/Googleprojectgen-lang-client-0020540057 giữ nguyên FreeOnly. Preflight phải PASS proof/readiness/localquota/noactiveoverlappingtest; guardblock/429 thì dừng, không paidfallback/bậtbilling. Local Main/Stage ledgers tách nhưng Googleproject quota chia sẻ. Tối đa12reservations tương đương2.4%hạnmức500RPD đã cấu hình, không phải chứng minh quota thực tế còn đủ. Không gọi SDK chỉ để preflight.

## Điều kiện PASS

Native actor/project đúng; plan BA+QA; providerreceipts LIVE_SUCCESS/modelmetadata/usage thật; Reviewer kiểm Nativecitations; kết quả xuất hiện ở Assistant và Monitor; graph/Timeline/FinalReport nêu đúngLIVE_GEMINI. NoWPwrite, không gắn receipt giả vào execution cũ. Đọc trạng thái lỗi/partial trung thực; không coi HTTP200 hoặc backendCOMPLETED là đủ khi UI chưa hiển thị.

Backup/fingerprints hiện hành trước submit; ghi runID/trace/receiptcounts/beforeafterusage/screenshot sau khi hoàn tất. Không restart/deploy container. Thao tác này cần phê duyệt riêng theo mụcXIII takeover; câu trả lời Owner cho smoke2requests trước không cấp quyền cho lượt này.
