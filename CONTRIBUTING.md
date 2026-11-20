# Đóng góp

1. Đọc `AGENTS.md`, `CONTEXT.md`, `architecture.md` và README của module liên quan.
2. Pull cập nhật: `git pull --ff-only`. Tạo branch `codex/<muc-dich>` hoặc branch theo quy ước nhóm.
3. Giữ diff nhỏ; không đưa dữ liệu runtime, secrets, backup hay đánh giá cá nhân vào Git.
4. Cập nhật thiết kế trong `architecture.md` nếu thay đổi thiết kế/hành vi hệ thống; bổ sung regression test khi phù hợp.
5. Stage các file đã xem bằng `git add <file>`; chạy `python scripts/check_publication.py` để quét đúng Git index, tests đúng phạm vi và `git diff --cached --check`. File chưa stage không thuộc kiểm tra index.
6. Mở pull request với mục tiêu, thay đổi, kết quả kiểm tra thực tế và rủi ro/rollback.

Chỉ merge khi đã xem diff và các check liên quan đạt. Không force-push shared branches; không chạy live harness để thử một PR chưa được kiểm tra. Quyền GitHub không thay thế quyền Jira hoặc phê duyệt thay đổi dữ liệu nghiệp vụ.

Không gửi secrets hoặc dữ liệu công ty trong issue/PR. Các kiểm tra tích hợp cần credentials chỉ chạy riêng ở môi trường được cấp quyền.
