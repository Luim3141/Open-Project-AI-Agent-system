# HỒ SƠ PHÁP Y M5: BẢN ĐỒ ÁNH XẠ KỸ NĂNG CỦA CÁC TÁC NHÂN (AGENT SKILL MAPPING)
> Thời điểm kiểm toán: `2026-10-30 20:30:54 UTC`  
> Thư mục kỹ năng: `openproject/ai/engineering_skills/` & `~/engineering/feedback-.../skills/`

---

## 1. MA TRẬN ÁNH XẠ KỸ NĂNG VÀO TÁC NHÂN (SKILL MAPPING TABLE)

| Tên Kỹ Năng (Skill Name) | File Định Nghĩa | Gán Cho Tác Nhân (Agent) | Môi Trường Thực Thi | Mục Tiêu & Trách Nhiệm Kỹ Thuật |
| :--- | :--- | :--- | :--- | :--- |
| **`engineering-planning`** | `engineering_skills/engineering-planning/SKILL.md` | **Supervisor, PM, BA** | Python Gateway (Docker) | Phân tích yêu cầu, phân rã WBS, sinh tiêu chí chấp nhận Gherkin ACs. |
| **`engineering-development`** | `engineering_skills/engineering-development/SKILL.md` | **Dev Agent** | OpenClaw WSL2 Daemon | Thực thi mã nguồn, tuân thủ TDD (RED/GREEN), quản lý Git branch/commit. |
| **`engineering-review`** | `engineering_skills/engineering-review/SKILL.md` | **Reviewer Agent** | OpenClaw WSL2 / Local Policy | Rà soát exact unified diff, đối chiếu tiêu chí chấp nhận, phát hiện lỗi bảo mật. |
| **`engineering-qa`** | `engineering_skills/engineering-qa/SKILL.md` | **QA Agent** | OpenClaw WSL2 Daemon | Chạy kiểm thử tự động pytest, thu thập exit code, sinh artifact XML. |

---

## 2. NỘI DUNG CỐT LÕI CỦA CÁC ĐẶC TẢ KỸ NĂNG (SPEC HIGHLIGHTS)

1. **`engineering-planning`:**
   - Cấm context injection ngoài phạm vi task.
   - Trích xuất thông tin chỉ từ Native Backlog và Second Brain RAG.
2. **`engineering-development`:**
   - Yêu cầu viết behavioral pytest trước khi code.
   - Bắt buộc lưu trữ bằng chứng failure (assertion error) và pass.
3. **`engineering-review`:**
   - 0 LLM Calls. So sánh trực tiếp unified diff với AC checklist.
   - Trích dẫn chính xác file và số dòng bị lỗi, cấm nhận xét chung chung.
4. **`engineering-qa`:**
   - Chạy test trong môi trường `.venv` cô lập.
   - Xuất file artifact `acceptance-0.xml` làm bằng chứng pháp lý nghiệm thu.
