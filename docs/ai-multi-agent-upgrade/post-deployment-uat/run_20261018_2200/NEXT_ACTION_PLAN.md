# Hành động tiếp theo

1. Human-UAT các chức năng local qua URL trong UAT_EXECUTION_REPORT.md. Dùng đúng account private hiện có; không gửi password/TOTP seed vào chat. Ghi ví dụ đầu vào, role, mong đợi/thực tế và run_id khi thấy lỗi.
2. G2: owner xác minh đúng project/model, Free/No billing account/không billing và quota hiện tại. Chỉ sau đó xin duyệt smoke nhỏ: đúng1generateContent trên model/key hiện có; input “Reply exactly QLDAPM_UAT_OK”, max_output_tokens16, không tool/grounding/dữ liệu công việc, không retry hoặc paid fallback. Ghi ledger trước/sau, HTTP/status/tokens; dừng401/429/503 hoặc proof không hợp lệ. Đây là đề xuất, chưa được duyệt và chưa gọi.
3. Nếu cần trải nghiệm draft→proposal liền mạch, thêm một bước PM “Tạo preview từ draft” với server-side fresh ACL/type/native lockVersion, canonical hash, người dùng xem diff rồi approve/reject. Không tự thực hiện draft text, không auto-approve. Qualify clone trước; deployment gián đoạn cần owner duyệt riêng.
4. Cải thiện trình bày Markdown bằng renderer giới hạn/escaped output và regression XSS; đây là P3, chưa sửa/deploy trong rollout Gateway-only này.
5. Nếu nghiệm thu lifecycle Scrum, tạo Sprint fixture riêng trên owned clone để test start/complete/reassignment/PM ceiling. Không dùng S1–S5 đang phục vụ làm fixture.

Không chạy lại provision sau resume:477 đã deployed verified. Đọc CHECKPOINT.md/LATEST.json/fix-serving-apply.json trước hành động. Không rotate TOTP, không reset Git/DB/quotas, không mở billing, không thay Quick Tunnel/Main/CSDLDPT. Không chạy qualify_remaining.py prepare/resume vì có thể cấp lại synthetic fixture tokens. Clone hiện stopped và dữ liệu giữ, muốn sử dụng lại cần inspect trước.
