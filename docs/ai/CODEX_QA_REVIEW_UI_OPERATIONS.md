# Human QA review — Main

1. Mở AI Assistant, tìm **AI Control Center**, chọn **Bằng chứng QA / Kiểm duyệt** cạnh Execution Monitor. PM/Owner và QA thấy lối vào; quyền server vẫn kiểm tra lại.
2. QA tạo record qua `qa_evidence_capture` từ Native activity/attachment thực do chính QA tạo, lấy `id` kết quả. Tool này không xuất hiện cho Owner. Không dùng nội dung giả, model run ID tự khai hoặc kết quả kiểm thử chưa chạy.
3. Nhập ID vào trang QA và chọn **Đọc bằng chứng**. Trang hiển thị criteria Native, expected/actual/outcome, author, version, activity, artifact SHA và exact review hash. Nội dung chỉ là manual attestation, không tự trở thành automated proof.
4. PM/Owner độc lập với QA và assignee đọc nội dung, tick xác nhận rồi chấp nhận hoặc từ chối. Nguồn cũ không được chấp nhận; review đã quyết định không được replay. Không có auto-review tool. Quyết định chỉ cập nhật ledger và audit, không sửa WP.
5. Sau review, `qa_transition_prepare` vẫn cần accepted/current/all-PASSED evidence và Native form hợp lệ, rồi tạo proposal riêng. Mỗi Native execution cần exact proposal/hash approval mới; Core gates vẫn kiểm tra khi ghi. Lỗi409 cần đọc lại, không blind retry. Nếu kết quả chưa rõ, giữ unknown và đối soát.

Hiện Main có0QA evidence và0review mới. Page UAT và isolated positive tests không phải business QA PASS. Task371 còn thiếu story/AC/scope evidence/approval cho bước IN ANALYSIS; không chuyển thẳng REVIEW hoặc điền evidence giả để đóng test. Xem `CODEX_WF11_CURRENT_NATIVE_READINESS.json`.

QA23 hiện có Native comment link nhưng không được quảng bá attachment upload link trên375. Vì V1 cần attachment do chính QA tạo, phần producer còn là gap; không dùng attachment của Owner thay thế. Phương án inline log trong Native comment chỉ là design preview tại `CODEX_WF11_NATIVE_QA_PRODUCER_DESIGN_PREVIEW.md`, chưa triển khai. Không cần và không được tự cấp quyền edit WP cho QA để vượt gap này.

Không cần chuyển sang ba-pm để Owner review. Không cần đổi password/TOTP/token hoặc dùng n8n editor cookie. External notifications, Native relation/deletion và full DR vẫn chịu blocker riêng. Tất cả approval cũ đã consumed.
