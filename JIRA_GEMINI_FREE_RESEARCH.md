# Gemini Free Tier — Jira bot read-only

Kiểm chứng tài liệu: 2026-10-09. Phạm vi: Gemini Developer API; không nghiên cứu triển khai `generateContent`.

## Ràng buộc và trạng thái thực tế

Theo yêu cầu: budget **0**; Gemini chỉ optional; không đổi billing, gọi API, đọc credentials, ghi Jira hoặc chia sẻ đánh giá nhân sự. Chỉ tạo note này; không sửa tools/tests.

**Project billing, tier, region và quota thực tế: UNKNOWN.** Không kiểm tra tài khoản. API key kế thừa billing/tier của project, không có billing riêng; có key không chứng minh miễn phí. [Billing](https://ai.google.dev/gemini-api/docs/billing#projects-and-api-keys)

## Billing / miễn phí

Tài khoản mới bắt đầu Free Tier, chỉ truy cập một số model trong quota miễn phí. Chuyển Paid Tier cần liên kết billing; luồng Prepay yêu cầu tối thiểu $5, có trường hợp Postpay. Spend cap có độ trễ khoảng 10 phút, có thể vượt cap: không phải bảo đảm chi phí 0. [Billing](https://ai.google.dev/gemini-api/docs/billing)

Adapter main chọn `gemini-3.1-flash-lite`: bảng Standard có Free Tier input/output miễn phí, nhưng không chứng minh model/quota khả dụng hoặc billing tier của project người dùng. Không lấy giá Free của model để bảo đảm key bất kỳ không bị tính phí. [Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite)

## Privacy / data-use

Unpaid Services: Google dùng input/output cải thiện sản phẩm/ML; human reviewers có thể đọc, xử lý sau khi tách account/key/project. Điều khoản yêu cầu không gửi dữ liệu sensitive, confidential hoặc personal. [Terms — Unpaid Services](https://ai.google.dev/gemini-api/terms#unpaid-services)

Paid Services không dùng prompts/responses cải thiện sản phẩm, nhưng vẫn log tạm chống lạm dụng/pháp lý; API project có active billing thuộc Paid Services. EEA/UK/Switzerland áp dụng data-use Paid cả unpaid quota; API Clients phục vụ người dùng tại đó chỉ dùng Paid Services. Region: UNKNOWN, không suy từ timezone. [Terms](https://ai.google.dev/gemini-api/terms)

## Rate limits

Quota gồm RPM, input TPM, RPD; vượt bất kỳ giới hạn nào gây lỗi. Áp dụng theo project, không theo key; RPD reset nửa đêm Pacific. Giới hạn phụ thuộc model/tier; preview/experimental chặt hơn. Quota active xem trong AI Studio; capacity không được bảo đảm. Không chốt số RPM/TPM/RPD cho project UNKNOWN hoặc dùng quota Grounding làm quota sinh văn bản. [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## Khuyến nghị cho main agent

Đây là khuyến nghị, chưa triển khai: chưa xác minh Free Tier thì giữ Gemini tắt và dùng báo cáo local; không auto-upgrade/top-up hoặc chuyển model trả phí. Gặp quota/lỗi thì fallback local, retry có giới hạn.

Chỉ gửi số liệu tổng hợp không nhạy cảm, được phép chia sẻ: counts theo status, tỷ lệ hoàn thành, blockers đã làm sạch. Không gửi tên/email/accountId, worklogs cá nhân, comments/descriptions thô, secrets hoặc personnel reviews; mã giả không tự bảo đảm ẩn danh. Bot chạy local vẫn gửi payload ra Google nếu bật adapter, nên giảm dữ liệu theo cảnh báo Unpaid Services. [Terms](https://ai.google.dev/gemini-api/terms#unpaid-services)

Ranh giới quyền theo yêu cầu: Gemini chỉ diễn đạt tiến độ; key Gemini không cấp Jira admin. Quyền Jira độc lập; không thực thi output model thành Jira writes.
