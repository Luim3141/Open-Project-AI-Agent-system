# Báo Cáo Nghiệm Thu Task P05-04: BA Agent

**Mã Task:** P05-04  
**Giai đoạn:** Phase P05 — Multi-agent Supervisor + PM/BA/QA/DEV/Reviewer  
**Tiêu đề:** BA Agent: User Stories/AC/ambiguity/dependency draft  
**Tiêu chí chấp nhận:** 5 golden cases PASS, cite native IDs và không tự ghi  
**Thời gian hoàn thành:** 2026-10-17  
**Người thực hiện:** Gemini (kế thừa từ Codex)  
**Trạng thái:** PASS (5/5 golden test cases)

---

## 1. Mục Tiêu & Phạm Vi Triển Khai

BA Agent là tác nhân chuyên biệt phụ trách phân tích nghiệp vụ và chất lượng yêu cầu trong kiến trúc Multi-Agent của QLDAPM Local V2:
1. **Chuẩn hóa User Story (User Story Decomposition):** Chuyển đổi các mô tả tự do/chưa chuẩn hóa thành cấu trúc User Story chuẩn: "Là [Vai trò]... Tôi muốn [Tính năng]... Để [Mục đích/Giá trị]...", kèm trích dẫn nguồn native ID (`work_package_id`, `lock_version`).
2. **Soạn thảo Tiêu chí chấp nhận (Acceptance Criteria - AC):** Biên soạn bộ tiêu chí kiểm thử rõ ràng theo chuẩn Given-When-Then hoặc checklist bao gồm luồng chính (happy path), luồng ngoại lệ và ràng buộc phi chức năng.
3. **Phát hiện yêu cầu mơ hồ (Ambiguity Detection):** Tự động rà soát các thuật ngữ định tính/mơ hồ (ví dụ: "thật nhanh", "giao diện đẹp", "tự hiểu", "tối ưu"), cảnh báo và đưa ra câu hỏi làm rõ (clarifying questions) cho PM và các bên liên quan.
4. **Phân tích phụ thuộc nghiệp vụ (Business Dependency Mapping):** Rà soát quan hệ phụ thuộc giữa các tính năng (ví dụ tính năng B phụ thuộc vào Đăng nhập/Xác thực A), trích dẫn đầy đủ ID của các work package tham gia quan hệ.
5. **Quy tắc nghiêm ngặt KHÔNG tự ý ghi (Strict No Self-Write):** Tương tự PM Agent, BA Agent là tác nhân tham vấn & phân tích. Khi nhận lệnh yêu cầu ghi hoặc sửa đổi trực tiếp dữ liệu OpenProject, agent từ chối thực thi trực tiếp, trả trạng thái `REVIEW`, đính kèm bản dự thảo đề xuất (Proposal Draft) và trích dẫn `NativeReference` (ID + lock_version) để trình người dùng phê duyệt theo quy trình PM-only-write.

---

## 2. Thiết Kế & Mã Nguồn

- Module nghiệp vụ: `openproject/ai/gateway/ba_agent.py`
  - `draft_user_story(package)` -> Trả về cấu trúc User Story chuẩn + `NativeReference`.
  - `draft_acceptance_criteria(package)` -> Trả về danh sách AC testable + `NativeReference`.
  - `detect_ambiguity(package)` -> Phát hiện từ mơ hồ + câu hỏi làm rõ + `NativeReference`.
  - `draft_dependencies(packages)` -> Lập sơ đồ phụ thuộc nghiệp vụ + danh sách `NativeReference`.
  - `BAAgent.run(task, scope, packages)` -> Điều phối thực thi, chặn write intent chuyển thành Proposal Draft, trả về `AgentResult`.
- Triết lý **Ponytail**: Tận dụng 100% Pydantic models hiện hữu (`AgentTask`, `AgentResult`, `NativeReference`), 0 dependency mới, 0 cuộc gọi Gemini tốn phí nếu chạy deterministic.

---

## 3. Bằng Chứng Kiểm Thử (5 Golden Cases)

File kiểm thử: `openproject/ai/tests/test_ba_agent.py`

| STT | Golden Case | Mô Tả & Điều Kiện Kiểm Chứng | Kết Quả | Thời Gian |
|---|---|---|---|---|
| 1 | `test_golden_case_1_user_story_decomposition_with_native_citation` | Chuẩn hóa mô tả công việc thô #201 thành User Story chuẩn "Là... Tôi muốn... Để...", trích dẫn đúng lock_version 2. | **PASS** | 0.000s |
| 2 | `test_golden_case_2_acceptance_criteria_drafting` | Soạn thảo bộ 3 tiêu chí AC (Giao diện, Happy Path, Ngoại lệ) cho công việc #202, trích dẫn lock_version 4. | **PASS** | 0.000s |
| 3 | `test_golden_case_3_ambiguity_detection_and_flagging` | Phát hiện chính xác các từ mơ hồ "thật nhanh", "giao diện đẹp", "tự hiểu" trong task #201 và xuất 2 câu hỏi làm rõ. | **PASS** | 0.000s |
| 4 | `test_golden_case_4_business_dependency_drafting` | Phát hiện quan hệ nghiệp vụ giữa xuất báo cáo #203 và đăng nhập #201, trích dẫn đầy đủ cả hai mã ID. | **PASS** | 0.000s |
| 5 | `test_golden_case_5_strict_no_self_write_mutation_refusal` | Nhận lệnh "Cập nhật AC này vào mô tả task #202 ngay", từ chối mutation, trả trạng thái `REVIEW`, xuất Proposal Draft trích dẫn #202 lockVersion 4. | **PASS** | 0.000s |

**Tổng kiểm thử BA Agent:** 5/5 tests PASS (0.001s).
