# Chủ dự án nghiệm thu — 5 người, Windows + Docker Desktop, 0 phí mới

## A. Thao tác startup bình thường (bắt buộc)

- Sau khi Codex setup lần đầu, Windows đã chạy nhưng Docker Desktop đang tắt. Chủ máy mở **Docker Desktop**. KHÔNG chạy PowerShell, KHÔNG chỉnh Task Scheduler, KHÔNG mở command prompt, KHÔNG nhập lại Gemini key.
- Chờ healthy trong thời gian thực đo; từ 5 máy LAN đã được setup HTTPS một lần, mỗi người đăng nhập đúng account và thấy OpenProject/AI. N8n workflow, agent runtime, Gateway tự lên. Test 3 lần stop/start Docker engine (không manually stop containers).
- Nếu một container đã stop thủ công thì `Repair-QLDAPM-Local.ps1` là ngoại lệ admin được ghi rõ, không giả vờ Docker restart sẽ cứu mọi trường hợp.

## B. Gemini Free Tier và multi-agent

- Chứng minh model/project API được phép Free; 5 người cùng yêu cầu AI thì xếp hàng công bằng, Gemini Pro subscription không được dùng như API credit. 429/503: UI báo WAITING, không gọi paid, không cần setup lại credentials sau restart.
- Hỏi 'Có bao nhiêu task chưa Done?' → native query không đốt LLM. Hỏi 'Vì sao chậm và giải quyết ra sao?' → Supervisor chỉ gọi agent cần thiết, có references.

## C. RBAC và đề xuất

- PM yêu cầu đề xuất điều chỉnh Sprint: PM/BA/QA/DEV/Reviewer phối hợp, tạo proposal; PM thật xác nhận mới viết qua native Core. BA/FE/BE/QA cùng nội dung không thể ghi task/role bất hợp lệ.

## D. n8n local workflow, không GitHub Research

- Daily Sprint brief, deadline/blocker alert, workload issue, missing AC/test readiness và weekly internal digest đều là workflows **nội bộ**. 5 người xem tại QLDAPM theo quyền; chỉ 1 local n8n admin quản lý editor, không chia paid seats.
- Docker bị tắt qua giờ schedule: khi mở lại không gửi trùng hoặc bắn dồn sự kiện; Gemini quota thiếu thì report deterministic vẫn có.

## E. Second Brain nội bộ

- Hỏi lý do một task blocked → trích đúng note/AC/comment theo role; nguồn + timestamp; từ chối nếu không đủ quyền. Ticket có prompt injection không thể biến thành instruction/system admin.

## F. Local release

- Sau staging test, owner cho phép promote main local nếu đã có backup/rollback. Không VPS/scale/public WAN. Kết luận phải có trạng thái từng task, số liệu sử dụng API thực, log start Docker và test 5 roles.
