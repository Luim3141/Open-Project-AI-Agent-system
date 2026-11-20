# Quyết định QA / Native còn cần

Hai human reviews QA23→PM19 của evidence375v0 đã hoàn tất và còn current. Không yêu cầu lặp lại. Người dùng đã xác nhận chính họ đổi password và enroll TOTP của QA23 khi first-login; không có yêu cầu credentials mới.

Hiện không có Native proposal mới được cấp phép. Mọi create/update/transition/relation/permanent delete trên Main cần proposal mới hợp lệ, đúng actor/resource/payload/version/hash và human decision được hệ thống xác thực. Các approval lịch sử đều consumed; việc review QA không tự cho phép Native write.

Chưa chuẩn bị một approval “đóng bug” vì source/fix/phase prerequisites chưa đủ. Cần hoàn thiện Native-compatible phase contracts và proof thực trước khi xin một quyết định có thể review được. Không tạo proposal invalid chỉ để yêu cầu người dùng duyệt. Với packet mới cần review, QA và Manager phải dùng danh tính riêng, independent với producer/assignee theo policy; Owner không tự review artifact của mình.

Trusted-delete đã deploy kỹ thuật với ledger rỗng và kiểm chứng trên clone. Không có yêu cầu xóa Main; không tái dùng #370 hoặc cây #371–#375 để thử xóa. External notifications và full Qdrant restore là các blocker riêng, không được suy diễn approval.
