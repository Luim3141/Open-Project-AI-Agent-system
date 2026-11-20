# BÁO CÁO ĐỐI CHIẾU KIẾN TRÚC VÀ NĂNG LỰC UPSTREAM (UPSTREAM CAPABILITY PARITY)
**Hệ thống nghiên cứu:** Paperclip (`paperclipai/paperclip`), Agency Agents (`msitarzewski/agency-agents`), Superpowers (`obra/superpowers`)  
**Mục tiêu:** Phân tích thực chất các cơ chế kiến trúc giá trị cao của ba hệ thống mã nguồn mở, so sánh đối chiếu với QLDAPM MAIN, lập bảng ma trận năng lực và chỉ ra lộ trình hiện thực hóa chi tiết trong Phase 2.6.

---

## 1. Nghiên Cứu Chi Tiết Từng Hệ Thống Upstream

### 1.1. Paperclip (`paperclipai/paperclip`)
- **Bản chất kiến trúc:** Hệ thống điều phối tác vụ AI (Agent Task Orchestration) tập trung vào tính bền vững (durability), phân quyền sở hữu tác vụ (task ownership), bảo đảm ngân sách (budget governance) và ngăn chặn chạy phân mảnh (split-brain prevention).
- **Các cơ chế cốt lõi:**
  1. *Task Ownership & Atomic Claim:* Tác vụ khi vào hàng đợi phải có chủ sở hữu duy nhất (`owner`). Worker nhận việc phải thực hiện atomic lease (thuê có thời hạn với khóa đồng thời); không cho phép 2 worker cùng claim 1 unit.
  2. *Heartbeat Protocol:* Worker gửi tín hiệu sống định kỳ. Nếu worker chết hoặc mất kết nối quá thời gian TTL, hệ thống kích hoạt cơ chế hồi phục (lease recovery), chuyển trạng thái sang `STALE` hoặc trả lại hàng đợi.
  3. *Budget Governance:* Quản lý trần tài nguyên (tokens, requests, execution time) theo từng vai trò, không cho phép agent tự động retry vô hạn làm cạn kiệt ngân sách.
  4. *Durable Checkpoints & Nonce Idempotency:* Mọi bước thực thi đều được ghi vết kèm checkpoint version và idempotency key. Khôi phục (`resume`) chỉ diễn ra từ điểm kiểm tra đã xác minh.

### 1.2. Agency Agents (`msitarzewski/agency-agents`)
- **Bản chất kiến trúc:** Khung tổ chức đội ngũ Agent chuyên môn hóa cao (Specialized Multi-Agent Roster) theo cấu trúc phòng ban công nghệ thực tế, loại bỏ hoàn toàn mô hình "Monolithic God-Agent".
- **Các cơ chế cốt lõi:**
  1. *Phân định vai trò độc lập (Role Specialization):*
     - **Project Manager (PM):** Quản lý tiến độ, ưu tiên backlog, phân rã WBS, giao việc cho Dev, xác thực Definition of Done.
     - **Business Analyst (BA):** Phân tích yêu cầu, xây dựng User Story, Acceptance Criteria (AC), API contract và edge cases.
     - **Developer (Dev):** Chỉ tập trung vào việc đọc AC, viết mã nguồn, kiểm thử đơn vị trong môi trường sandbox cô lập.
     - **Code Reviewer:** Kiểm tra mã độc lập với Dev, rà soát diff thực tế theo chuẩn bảo mật, cấu trúc dữ liệu, không duyệt mã mù quáng.
     - **Quality Assurance (QA):** Thực thi bộ kiểm thử chấp nhận độc lập (E2E/Integration test), đối soát từng tiêu chí AC.
     - **Analytics / Project Reporter:** Thu thập số liệu vận hành thực tế (WIP, lead time, defects, commits, pull requests, token consumption) để tạo báo cáo tiến độ minh bạch cho lãnh đạo.
  2. *Context Isolation & Structured Handoff:* Ngữ cảnh của mỗi Agent được phân tách nghiêm ngặt. Handoff giữa các Agent là các bản hợp đồng dữ liệu có cấu trúc (JSON schema/manifest), không phụ thuộc vào chuỗi hội thoại dài gây loãng thông tin.

### 1.3. Superpowers (`obra/superpowers`)
- **Bản chất kiến trúc:** Hệ thống phương pháp luận kỹ thuật phần mềm có kỷ luật (Engineering Process Discipline) được đóng gói thành các kỹ năng thực thi cho Agent.
- **Các cơ chế cốt lõi:**
  1. *`writing-plans` & `brainstorming`:* Lập kế hoạch phân tích nguyên tử trước khi chạm vào mã nguồn. Đảm bảo mọi bước đều có kiểm chứng.
  2. *`using-git-worktrees`:* Cách ly không gian làm việc bằng Git worktrees, bảo vệ branch chính và tránh xung đột mã.
  3. *`test-driven-development` (TDD):* Viết test hành vi trước (RED) → triển khai lượng mã tối thiểu (GREEN) → chuẩn hóa mã sạch (REFACTOR).
  4. *`systematic-debugging`:* Khắc phục lỗi có hệ thống: Triệu chứng → Bằng chứng → Một giả thuyết duy nhất → Thử nghiệm có thể đảo ngược → Sửa gốc rễ → Kiểm chứng không gây hồi quy (regression).
  5. *`verification-before-completion`:* Chỉ tuyên bố hoàn thành khi có bằng chứng thực tế từ lệnh thực thi và kiểm thử độc lập, không chấp nhận khẳng định bằng văn bản thuần túy.

---

## 2. Ma Trận Đối Chiếu Năng Lực (Parity Matrix)

| Năng Lực / Cơ Chế | Paperclip | Agency Agents | Superpowers | Trạng Thái QLDAPM MAIN | Thành Phần Hiện Thực Hóa Tại QLDAPM |
|---|:---:|:---:|:---:|:---:|---|
| **Atomic Claim & Queue** | Có | - | - | **IMPLEMENTED** | `gateway/engineering.py::admit/claim`, `gateway/store.py::claim_run` (SQLite atomic lock) |
| **Worker Heartbeat & TTL** | Có | - | - | **IMPLEMENTED** | Windows Task Scheduler `QLDAPMEngineeringDelivery`, `gateway/engineering_lifecycle.py::heartbeat` (TTL 30s) |
| **Budget & RPM/TPM Gate** | Có | - | - | **IMPLEMENTED** | `gateway/gemini.py::reserve_budget`, `gateway/live_agents.py`, Gemini Free Tier limiter |
| **Multi-Agent Roster (PM, BA, Dev, Reviewer, QA)** | - | Có | - | **IMPLEMENTED** | `gateway/engineering_personas.py`, OpenClaw runtime (`/home/openclaw/.openclaw/openclaw.json`) |
| **Analytics & Project Reporting** | - | Có | - | **IN PROGRESS (M7)** | Module `gateway/engineering_reporting.py` (Daily, Weekly, On-Demand, UI Control Center) |
| **Context Isolation & Handoff** | - | Có | - | **IMPLEMENTED** | SQLite receipts, artifact bundles trong `docs/ai/engineering/runs/<id>/` |
| **Git Worktrees Isolation** | - | - | Có | **IMPLEMENTED** | WSL2 linked ext4 worktree (`/home/openclaw/engineering/create-list-persistence-v1`), branch tracking |
| **TDD & Systematic Debugging** | - | - | Có | **IMPLEMENTED** | Pytest suites trong repo demo, `test_owner_project_authority.py`, `test_engineering_*.py` |
| **Independent Code Review & QA Gate** | - | Có | Có | **IMPLEMENTED** | `engineering_skills/engineering-review/SKILL.md`, `engineering_skills/engineering-qa/SKILL.md` |
| **State Sync Contract (SSOT)** | Có | - | - | **IMPLEMENTED** | `gateway/engineering_state_sync.py` (5 state groups, OpenProject Native status transition graph) |
| **Two-Way GitHub Sync** | - | - | - | **IMPLEMENTED (M4 Upgrade)** | `gateway/engineering_github_sync.py` (Polled sync, PR #1–#4 tracking, stacked branch awareness) |

---

## 3. Các Khoảng Trống (Gaps) Và Lộ Trình Hiện Thực Hóa Trong Phase 2.6

1. **Khoảng trống 1: Hệ thống Báo cáo Tiến độ Toàn diện (Từ Agency Agents Reporting Role):**
   - *Hiện trạng:* Đã có các chỉ số thô trong SQLite và OpenProject, nhưng chưa có hệ thống báo cáo tiến độ tự động (Daily/Weekly/On-demand) trực quan hóa ngay trên giao diện OpenProject.
   - *Giải pháp Phase 2.6 (Milestone 7):* Xây dựng `openproject/ai/gateway/engineering_reporting.py` tổng hợp dữ liệu factual deterministic từ DB, commit, PR, runs; tích hợp tùy chọn phân tích rủi ro của Gemini; lưu trữ lịch sử báo cáo và hiển thị trên tab "Reports" tại UI Control Center.
2. **Khoảng trống 2: Nâng cấp GitHub Sync nhận biết Stacked PRs (Từ Paperclip/Superpowers):**
   - *Hiện trạng:* Đã có sync trạng thái PR, nhưng chưa phân biệt rõ ràng giữa `merged-to-feature-branch` (PR #2) và `merged-to-main`.
   - *Giải pháp Phase 2.6 (Milestone 4):* Nâng cấp `engineering_github_sync.py` để theo dõi `baseRefName`, `mergeStateStatus`, review verdicts, CI checks rollup và loại trừ nguy cơ sync loop.
3. **Khoảng trống 3: Thử nghiệm Auto Mode với Backlog Unit mới (Từ Paperclip Autonomous Execution):**
   - *Hiện trạng:* Auto Mode đã kiểm chứng tính năng an toàn tự tắt khi `ALL_DELIVERED`, cần thử nghiệm trên backlog unit mới để chứng minh khả năng tự claim, lập kế hoạch, code, review và QA trọn vẹn.
   - *Giải pháp Phase 2.6 (Milestone 5):* Bổ sung unit mới và kiểm chứng pipeline chạy tự động an toàn.

---

## 4. Kết Luận
QLDAPM MAIN đã tiếp thu và nội địa hóa một cách thực chất các tinh hoa kiến trúc của Paperclip, Agency Agents và Superpowers vào đúng nền tảng OpenProject + Gateway + OpenClaw + Gemini API, bảo đảm sự độc lập, tin cậy cao và an toàn tuyệt đối cho dữ liệu doanh nghiệp.
