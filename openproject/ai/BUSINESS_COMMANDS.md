# Dùng Gemini trong OpenProject staging

Mở http://localhost:18091/projects/qldapm-local/qldapm-ai bằng tài khoản thành viên đã đăng ký. Account admin portal dùng cho quản trị; hiện không nằm trong AI business registry.

## Ra lệnh bằng lời

| Mục đích | Ví dụ | Kiểm tra kết quả |
|---|---|---|
| Hiểu ticket | Đọc đầy đủ công việc 58, giải thích nghiệp vụ, acceptance criteria và điểm cần kiểm thử. | Câu trả lời tiếng Việt dựa trên mô tả, bình luận, quan hệ; phân tích AI là gợi ý. |
| Comment | Thêm comment vào công việc 58: Đã kiểm tra trên staging | Thông báo thành công và bình luận native. Comment mẫu này đã được ghi một lần, không gửi lại để thử. |
| Tạo Task | Tạo Task “Kiểm tra thu hồi quyền”, mô tả “Kiểm thử truy cập sau khi gỡ thành viên”, giao cho BE. | Tên, loại, người phụ trách và link công việc mới. |
| Tạo Subtask | Tạo Subtask dưới công việc 58, tên “Kiểm tra PM duy nhất”, giao cho QA. | Parent/type/assignee readback; tài khoản cần native manage_subtasks (staging PM đã có). |
| Sửa nhiều trường | Cập nhật công việc ID: đổi tên thành “...”, mô tả “...”, giao cho BE, ưu tiên High, hạn 2026-10-20. | Thông báo nêu các trường đã đổi; mở công việc để xem. Thay ID bằng ID thật. |
| Hạn tương đối | Cập nhật công việc ID: đặt hạn hoàn thành vào ngày mai. | AI dùng ngày dự án theo Asia/Bangkok; receipt hiển thị ngày YYYY-MM-DD thực tế. |
| Chuyển trạng thái | Chuyển công việc ID sang IN PROGRESS. | Native workflow/role/phiên bản phải cho phép; lỗi nêu rõ chưa thực hiện. |
| Lập backlog | Đề xuất chia công việc ID thành 3 Subtask, ghi mô tả/AC và vai trò phụ trách. | Đề xuất trước khi ghi; xem bảng thay đổi và duyệt từng đề xuất. |

## Checkbox và preview

Không bật checkbox: thao tác ghi tạo đề xuất, không tự ghi. Preview hiển thị tên thao tác và bảng “Hiện tại / Sau khi duyệt”; JSON/hash/receipt ở phần chi tiết kỹ thuật thu gọn. Đề xuất hết hạn cần tạo preview mới; đây là TTL an toàn của từng đề xuất, không phải expiry của Gemini.

Bật checkbox: không giới hạn cố định số tool calls, số vòng trao đổi với Gemini hoặc số ID trong một run; ordinary create/update/comment/transition theo yêu cầu và quyền native. Thời gian xử lý tối đa 600 giây, giới hạn tài nguyên và quota Gemini vẫn áp dụng; nếu bị ngắt, kết quả từng thao tác đã làm được lưu, không tự chạy lại. Ô ID có thể để trống khi câu lệnh ghi rõ ID. Nhập ô này để giới hạn các ID được sửa; giá trị nhập ưu tiên hơn việc suy ID từ câu lệnh. ID trong nội dung comment không tự cấp quyền. Source ID cho tạo mới có thể do host sinh; không cần nhớ lệnh JSON.

Gateway tra type/status/priority thật, đọc full description/comments/relations và các business scalar fields; không gửi profile, code, attachments hoặc credential fields sang Gemini. Các pattern password/token/key/contact được lọc; không nhập thông tin xác thực vào chat.

## Đọc thông báo

- Thành công: native API và readback đã xác nhận, có link công việc và nội dung đã đổi.
- Chờ duyệt: mới chuẩn bị thay đổi, chưa ghi.
- Hoàn thành một phần: một số thao tác đã có receipt, phần còn lại thất bại hoặc bị gián đoạn.
- Chưa thực hiện / chưa rõ kết quả: xem lý do và receipt trước khi gửi lại. Unknown write chặn các thao tác ghi tiếp trong cùng run; không replay tự động.

Gemini continuous authorization không hết hạn, key giữ backend. Quota/cooldown của Google và native workflow vẫn áp dụng. Xóa/admin/deploy/code không được checkbox ordinary writes tự cấp quyền. Live/Jira chưa đổi.

Bằng chứng và resume: [BUSINESS_CHECKPOINT_2026-10-15.md](BUSINESS_CHECKPOINT_2026-10-15.md).

Sửa lỗi 15/10: business tools truyền object có schema trực tiếp, không bắt Gemini nhét JSON vào chuỗi. List trả tóm tắt; đọc từng công việc vẫn lấy đầy đủ nội dung được phép. Local RPM/TPM theo phút sẽ hiển thị thời gian chờ rồi tự tiếp tục trước khi gửi request mới trong cùng run; không lặp thao tác đã có receipt. TPM dùng kết quả countTokens thay vì số byte UTF-8. Hết quota ngày hoặc Google từ chối vẫn báo rõ và giữ kết quả, không tự reset quota. Lỗi native form chỉ rõ trường và lý do, ví dụ thiếu quyền đặt công việc cha.


Cập nhật15/10 — ngày bắt đầu và nhận lệnh: PM có thể nói “set ngày bắt đầu và ngày kết thúc cho task442 từ15/10/2026 đến30/11/2026”, “thêm deadline cho subtask442 ngày31/12/2026”, hoặc “Subtasks442: đặt ngày bắt đầu…”. ID và plural/list được nhận trực tiếp; không cần bổ sung mô tả nghiệp vụ để sửa ngày. Ngày nghỉ có thể được native calendar điều chỉnh; duration có thể làm OpenProject tự tính ngày còn lại. Preview/receipt ghi rõ ngày thực tế và phần tự tính. Mỗi lượt là câu lệnh độc lập; nên ghi ID lại thay vì chỉ nói “việc đó”. Bật checkbox để thực hiện theo quyền PM, không bật để xem preview. Trạng thái đang xử lý không còn báo thiếu dữ liệu chỉ vì mới đọc được ticket.
