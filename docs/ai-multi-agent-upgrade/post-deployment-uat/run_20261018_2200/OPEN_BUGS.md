# Bug và hạn chế còn tồn tại

| ID | Mức độ | Trạng thái | Bằng chứng / xử lý |
|---|---|---|---|
| UAT-01 | P2 | FIXED_AND_VERIFIED_STAGING | Phủ định ghi bị regex nhận sai. Source planner,60Windows/41Linux,2clone UI và2serving UI regression PASS; rollout Gateway-only đã owner duyệt. fix-serving-apply.json + post-fix-serving-ui.json |
| UAT-02 | P3 | OPEN_PRESENTATION | Report Supervisor hiển thị các ký hiệu Markdown `###`, `**` dạng text. Nội dung/plan/receipt có thể đọc được, output được escape. Ảnh private post-fix-PM-result.png/post-fix-FE-result.png đã xem. Cần formatter an toàn + XSS/regression nếu cải thiện; không đưa raw HTML qua |
| DRAFT-CONVERSION | P2 functional gap | OPEN_NOT_IMPLEMENTED | Draft tư vấn không tự trở thành canonical executable proposal. Đường PM tool form/preview/approve/reject/audit đã thử thật; chưa có one-click conversion. Xem FUNCTIONAL_GAPS.md |
| DEF-08 historical TOTP claim | P1 tracked owner boundary | NOT_APPROVED_DO_NOT_ROTATE | Hiện old23–28 vẫn active/default,35–40 absent theo takeover recheck;5role đăng nhập TOTP hiện tại PASS. Không coi báo cáo Wave6 là proof rotation live, không tự rotate/close. Read-only projection hiện tại giữ nguyên |
| Native pre-auth HALError | P2 upstream diagnostic | NOT_REPRODUCED_AFTER_AUTH | Trace diagnostic trước auth/OTP chưa hợp lệ không phải product root cause; lượt auth chuẩn Native.me/time_entries200,0API/page errors. Không sửa Core từ trace này |

Backlog empty-screen/hidden error và n8n history timeout đã xác định là chờ/selector của harness, không đăng ký thành product bug mở. Mọi attempt FAIL vẫn giữ trong JSON lịch sử; kết quả cuối dùng rerun đã chỉ rõ. G2 là gate chờ owner, không được che bằng PASS từ mock.
