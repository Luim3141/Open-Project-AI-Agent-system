# BIÊN BẢN KIỂM TOÁN BASELINE PHÁP Y (PHASE 2.8 BASELINE AUDIT)
## DỰ ÁN: QLDAPM MAIN — PHASE 2.8
**Thời điểm lập:** 2026-10-30T19:30:00+07:00  
**Tác giả:** Gemini CLI (Lead Auditor & Principal Software Architect)  
**Mục đích:** Xác minh trung thực toàn bộ trạng thái hệ thống trước khi bắt đầu khắc phục các gaps của Phase 2.8.

---

## 1. THÔNG SỐ RUNTIME & MÃ NGUỒN HIỆN TẠI (CONFIRMED FACTS)

1. **Git Repository Status:**
   - Workspace: `D:\AI project\QLDAPM chat`
   - Branch: `codex/local-multi-agent-upgrade`
   - Git HEAD: `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`
   - Tracked files: CLEAN (`git diff --stat` rỗng 100%).
   - Demo Repository: `D:\AI project\QLDAPM-demo\mini-task-manager`
   - Branch: `codex/mini-task-manager-ready`, HEAD: `def9d0a8852af42a407bd42fb0051615a2de9331`.

2. **Docker Containers & Live Images:**
   - `qldapm-openproject-web-1`: Image `qldapm-core:engineering-continuation-r16-20261030` (Up, healthy).
   - `qldapm-ai-gateway-1`: Image `qldapm-ai:engineering-continuation-r16-20261030` (Up, healthy).
   - `qldapm-n8n-main`: `docker.n8n.io/n8nio/n8n:2.43.6` (Up, 16/16 workflows active).
   - `qldapm-qdrant`: `qdrant/qdrant:latest` (Up, green, 2,117 dense vectors).
   - `OpenClawGateway` (WSL2): Lắng nghe tại `127.0.0.1:18789`.
   - `Mini Task Manager`: Lắng nghe tại `127.0.0.1:18791` (HTTP 200).

3. **Current Engineering State:**
   - Engineering Mode: `OFF` (`engineering_control` = 6, 'OFF', updated 1793359412).
   - Active Queue: `0` (Không có job kẹt hay chạy nền).
   - Gemini Provider Gate: `OFF`/inactive (Không phát sinh cuộc gọi Gemini ngoài ý muốn).

4. **Project 5 Invariants Baseline (Chứng Minh Bất Biến Tuyệt Đối):**
   - Identifier: `qldapm-local` (ID: 5).
   - Số lượng Work Packages: đúng **341** items.
   - Dải ID: từ 38 đến 378.
   - Phân bố trạng thái: 340 items status=1 (New), 1 item status=37.
   - Max lock_version: 4.
   - **Thời điểm cập nhật mới nhất (latest_updated_at):** `2026-10-29T10:08:56Z` (chứng minh 0 mutation kể từ 29/10/2026).
   - Members: 5 users.
   - Dữ liệu chi tiết lưu tại `docs/ai/engineering/project5_invariants_baseline.json`.

---

## 2. CÁC ĐIỂM CHƯA ĐẦY ĐỦ BẰNG CHỨNG HOẶC LỆCH PHA (UNVERIFIED CLAIMS & DISCREPANCIES)

Qua kiểm toán độc lập đối chiếu với phản hồi của ChatGPT/Codex, ghi nhận 8 phát hiện kỹ thuật thực tế:

1. **Finding A (Auto Mode E2E):** `auto_mode_defect05_evidence.json` mới chỉ chứng minh logic Auto Shutoff khi backlog đã hoàn thành (`ALL_DELIVERED` -> `OFF`). Chưa chứng minh chu trình E2E khép kín của Auto Mode xử lý một Task mới thực tế từ OpenProject qua OpenClaw Dev/Reviewer/QA.
2. **Finding B (Reporting Scheduler Live Tick):** Scheduler kiểm tra hạn báo cáo chưa có worker/cron chạy tick tự động độc lập theo thời gian thực. Việc gọi `check_and_run_scheduled_reports` mới chỉ được gắn kèm khi có ai đó gọi API `engineering.status`. Cần một cơ chế timer/tick hoặc cron độc lập đảm bảo báo cáo được tạo tự động đúng giờ ngay cả khi không có request vào UI.
3. **Finding C (Dynamic Skills Execution):** Bằng chứng ở Phase 2.7 mới chỉ dừng lại ở cấu hình `openclaw.json` và phân quyền công cụ sandbox (deny write/edit). Cần chứng minh Agent thực sự đọc, thực hiện quy trình kỹ năng Superpowers (TDD, systematic debugging, code review, verification) với tool calls và artifacts tương ứng.
4. **Finding D (Owner Cross-Actor Resume):** Mới chỉ có test evidence Owner hủy (`cancel`) run của PM20. Chưa có live test cho thao tác `resume` run của PM20 và đọc lại trạng thái sau khi resume.
5. **Finding E (Project 5 Verification):** Trước đây chỉ đếm 341 WPs và thử 1 lệnh 403. Hiện đã trích xuất đầy đủ invariants baseline (341 IDs, lockVersions, latest updated 2026-10-29). Cần tái kiểm tra sau mọi thay đổi của Phase 2.8 để chứng minh invariants không đổi.
6. **Finding F (GitHub Reviews & CI Distinction):** Chưa kiểm tra chi tiết GitHub API endpoints (`/check-runs`, `/statuses`, `/actions/runs`, `/pulls/{n}/reviews`) để làm rõ lý do `NO_CI_CHECKS_CONFIGURED` và `NO_REVIEWS_ON_GITHUB`.
7. **Finding G (Reporting Schedule & Timezone UI Mismatch):**
   - Trong database `engineering_report_schedules`: `daily_hour = 7`, `daily_minute = 30`. Nhưng trên view `engineering.html.erb` dòng hiển thị lịch lại ghi cứng `Daily (08:00) · Weekly (Thứ 2, 09:00)`.
   - Tiêu đề báo cáo và trường thời gian hiển thị `11:13:14` (giờ UTC) thay vì `18:13:14` (giờ Việt Nam `Asia/Ho_Chi_Minh` UTC+7). Cần hiển thị động từ DB và chuẩn hóa múi giờ.
8. **Finding H (n8n & Second Brain Live Trace):** 16 workflows active và Qdrant green mới là health evidence. Cần có execution trace thực tế của WF04 và RAG semantic retrieval với trích dẫn chính xác.

---

## 3. RỦI RO ĐÃ XÁC ĐỊNH (KNOWN RISKS)

1. **Risk 1: Shared SQLite File Lock:** Mở `gateway.sqlite` từ bên ngoài host bằng tiến trình khác ở chế độ read-write có thể lock virtiofs mount khiến container gateway bị `sqlite3.OperationalError: unable to open database file`. **Giải pháp:** Chỉ mở `file:...mode=ro` trên host hoặc truy cập qua `docker exec`.
2. **Risk 2: Gemini API Quota Exhaustion:** Chạy E2E Auto Mode nhiều lượt có thể làm cạn quota free tier. **Giải pháp:** Thiết lập budget chặt chẽ, tối đa 1 lượt E2E trên 1 task fixture gọn gàng, có mock/playback an toàn nếu quota cạn.
3. **Risk 3: Task #379 & PR Merging:** Tuyệt đối không tự động merge PRs #1–#4 vào `main` và không tự đóng Work Package #379. Task mới thử nghiệm E2E phải là một Task con riêng biệt.

---

## 4. KẾ HOẠCH HÀNH ĐỘNG CÁC MILESTONE TIẾP THEO (ORDERED CHANGE PLAN)

1. **Milestone 1:** Fix Reporting Scheduler, Timezone `Asia/Ho_Chi_Minh`, Dynamic UI Binding, và xử lý xung đột với n8n WF07/WF12.
2. **Milestone 2:** Auto Mode End-to-End với Task mới độc lập trên Project 6 (từ OpenProject -> OpenClaw -> Git -> QA -> Status).
3. **Milestone 3:** Dynamic Skills thực chất (chứng minh Agent tuân thủ Superpowers procedures, phân biệt Installed/Read/Applied).
4. **Milestone 4:** Owner Full Control (hoàn thiện live cross-actor Resume và read-back state).
5. **Milestone 5:** GitHub Sync Correctness (phân biệt Check Runs, Statuses, Workflow Runs, Reviews).
6. **Milestone 6:** n8n WF04 Execution Trace & Second Brain RAG Semantic Retrieval Verification.
7. **Milestone 7:** Complete Browser Playwright UAT (kiểm thử tương tác sâu và chụp ảnh thực tế).
8. **Milestone 8:** Project 5 Data Invariants Re-Verification (đối chiếu baseline).
9. **Milestone 9:** Source / Deployment / Checkpoint / Handoff Package hoàn chỉnh tại `docs/ai/engineering/PHASE28_HANDOFF/`.

---
*Biên bản này được khóa và dùng làm căn cứ đối chiếu xuyên suốt Phase 2.8.*
