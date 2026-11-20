# Additional Live approval preview

Mục7 chỉ thị Owner yêu cầu xin riêng khi vượt6HTTP/3generations. Ngân sách gốc đã hết:6HTTP/3generations, hai read runs failed41d33283… và b566b115…; không được tự replay.

## Hành động duy nhất được đề nghị

Một run PM19 qua Native UI Main, engine gemini_read, checkbox WRITE=false, IDs367,50. Dùng nguyên prompt Owner: “Đọc Work Package #367 và Parent #50 bằng OpenProject Native. Phân tích kết quả kiểm thử CREATE trước đó, xác định mối quan hệ parent-child và assignee, trích dẫn dữ liệu thật. Không tạo, sửa, xóa hoặc bình luận bất kỳ công việc nào.”

- Thêm tối đa1countTokens +1generateContent (2Google HTTP),1generation, maxOutput3000, worker180s/call90s, retry0. Tổng cả phiên sau phê duyệt tối đa8HTTP/4generations.
- Model/key/project Free-only đã lưu; không billing/paid fallback. Gửi request và Native business context #367/#50 đã lọc; không user profiles/secrets, không gửi key trong nội dung.
- Native GET và final synthesis; model không có executable tools. Citations và parent/assignee facts phải khớp Native trước khi hiển thị. Không CREATE/PATCH/comment/delete; giữ367 và toàn bộ business data.
- Gateway `sha256:bcd7158e4febfd276d47599bf3be514997fbd976a32fb71be0f12b7d80748168`, Core `sha256:a3214219127e61ff934d33b0c45031df8a315e6a5f44ff9754c7985e2adcbcbb`, sourceSHA `0cc3f4e59c18fffc31c088d399078b4047328ba5707cc6a6a2eb902442eb70f6` đã deploy healthy, tests118Windows/114Linux/21browser PASS. Không cần deploy/restart thêm để chạy lượt này.
- Nếu quota/outage/validation fail: giữ lỗi, dừng, không gọi tiếp. Nếu browser timeout sau submit: đối chiếu run/ledger, không click gửi lại.

Phạm vi approval chỉ budget bổ sung này; không cấp Native mutation, không rearm Owner CREATE, không thay RBAC/key/model. Không cần Owner gửi credentials. Nếu Native PM session hết hạn thực tế mới cần Owner đăng nhập+TOTP.
