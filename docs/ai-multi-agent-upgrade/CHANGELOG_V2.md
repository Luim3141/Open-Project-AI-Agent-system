# Changelog V2 — điều chỉnh yêu cầu 15/10/2026

**So với bộ kế hoạch trước:**

1. BỎ toàn bộ yêu cầu **Windows boot/logon tự động khởi động Docker**. Thiết kế runtime mới: user chủ động mở Docker Desktop, các container đã provision tự chạy lại nhờ restart policy. Khi container bị manually stop, có `Repair-QLDAPM-Local.ps1` cho trường hợp đặc biệt.
2. Giữ **Gemini API key/project hiện có trong private runtime**, tự nạp lại; setup lần đầu kiểm chứng Free Tier. Không yêu cầu nhập key sau mỗi lần mở Docker. Nếu provider 429/503/key invalid thì hiển thị degraded, không gọi paid API.
3. Scope cố định **5 người dùng nội bộ trên cùng LAN**, PM/BA/FE/BE/QA; URL HTTPS nội bộ, chứng chỉ CA/trust thiết lập lần đầu; không public Internet/VPS.
4. BỎ toàn bộ **GitHub Research**, web crawler, coding agent tự thay source/deploy. Thay bằng Sprint reports, deadline risk, workload, AC/QA readiness, review nội bộ.
5. BỎ toàn bộ phase **P11** (Redis/Ollama/Langfuse heavy/local LLM/scaling/public LAN optional). Scope còn P00–P10, **113 task bắt buộc**; không hứa scale/HA.
6. Chỉ giữ **Google AI Pro sẵn có + Gemini API Free Tier đúng quyền và hạn mức thực**, dùng shared quota của 5 người, n8n Community selfhost, PostgreSQL FTS/local state. Không kích hoạt billing/credit/prepay hoặc paid SaaS.
7. Chuyển gate P10 từ “chỉ bàn giao staging” sang **local main release có owner approval, rollback**, không deploy VPS.
8. Thêm `FIVE_USER_LAN_ACCESS.md`, `GEMINI_FREE_QUOTA_PLAYBOOK.md`, task mới về LAN/TLS/privacy/runtime Gemini/5-user fairness, cập nhật acceptance matrix và runbook.
9. Cập nhật script dashboard thành policy manual Docker start. `TASKS.json` hoàn toàn TODO/0% vì chưa thực thi trên máy chủ của người dùng.

**Không xóa tiến độ thật nếu bản cũ đã được Codex triển khai**: hợp nhất theo mã task, giữ lại evidence/logs/versions/notes và kiểm thử lại các task đổi acceptance.
