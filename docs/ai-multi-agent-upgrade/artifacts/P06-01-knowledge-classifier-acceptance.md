# ACCEPTANCE REPORT: TASK P06-01 — INTERNAL KNOWLEDGE CLASSIFIER

- **Task ID:** `P06-01`
- **Phase:** `P06` (Second Brain nội bộ / FTS / ACL)
- **Tiêu đề:** Phân loại knowledge nội bộ: kiến trúc, ADR, work packages, AC, comments, sprint reports
- **Tiêu chí chấp nhận:** Chỉ index tài liệu/Work Package thuộc dự án được phép; không crawler GitHub hoặc web research.
- **Trạng thái:** `DONE` / `PASS`
- **Thời gian nghiệm thu:** 2026-10-17T11:55:00+07:00
- **Kỹ sư thực hiện:** Gemini (Google Antigravity)

---

## 1. Nội dung triển khai

Đã tạo module `openproject/ai/gateway/knowledge_classifier.py` cung cấp các tính năng:

1. **Phân loại 6 loại hình tri thức nội bộ (`KnowledgeDocType`):**
   - `ARCHITECTURE`: Tài liệu kiến trúc hệ thống (`architecture.md`, `ARCHITECTURE_TARGET.md`).
   - `ADR`: Quyết định kiến trúc (`docs/adr/0001-...`, `0002-...`, `0003-...`).
   - `WORK_PACKAGE`: Work packages nghiệp vụ từ OpenProject.
   - `ACCEPTANCE_CRITERIA`: Tiêu chí nghiệm thu định dạng Gherkin / Given-When-Then.
   - `COMMENT`: Thảo luận, ghi chú, trao đổi kỹ thuật trên từng Work Package.
   - `SPRINT_REPORT`: Báo cáo Sprint (mục tiêu, rủi ro, tiến độ).

2. **Kiểm soát ranh giới dự án & phân quyền ACL (`ALLOWED_PROJECTS`):**
   - Giới hạn cứng trong danh sách dự án hợp lệ được phép (mặc định: `QAG3`, `DEMO`, `DEMO-PROJECT`, `QLDAPM`).
   - Từ chối fail-closed đối với mọi tài liệu không có `project_id` hoặc thuộc dự án ngoài thẩm quyền (`SecurityValidationError`).
   - Gắn nhãn phân quyền truy cập `allowed_roles` (mặc định: `["PM", "BA", "FE", "BE", "QA"]`).

3. **Chốt chặn an toàn triệt để (Zero Crawler & No GitHub Research):**
   - Biểu thức chính quy `FORBIDDEN_CRAWL_PATTERN` kiểm tra và chặn đứng mọi đường dẫn URL ngoại vi (`http://`, `https://`), tên miền `github.com`, lệnh `git clone`, các từ khóa `crawler`, `scraper`, `spider`, `web research`.
   - Bảo đảm 100% dữ liệu được đưa vào Second Brain là nguồn tài liệu nội bộ hợp pháp trên máy local.

4. **Nguồn gốc xuất xứ (Provenance) & Hàm băm SHA256:**
   - Mỗi tài liệu đều được sinh mã băm SHA256 xác định từ bộ ba `(doc_type, source_id, content)` để phục vụ de-duplication và chống replay.
   - Trích xuất tự động AC và comments từ work package, gắn kèm `native_id` và `lock_version`.

---

## 2. Kết quả kiểm thử tự động

- **File test:** `openproject/ai/tests/test_knowledge_classifier.py`
- **Số test case:** 5/5 PASS (0.002s):
  1. `test_classify_valid_internal_types`: Phân loại chính xác ARCHITECTURE, ADR, SPRINT_REPORT.
  2. `test_reject_external_crawl_and_github`: Chặn thành công GitHub URLs và web crawling payload.
  3. `test_reject_disallowed_project_or_missing_project`: Chặn truy cập dự án trái phép và project rỗng.
  4. `test_classify_work_package_ac_and_comments`: Trích xuất đầy đủ WP, AC và Comments từ native work package dictionary.
  5. `test_deterministic_hash_integrity`: Xác minh tính toàn vẹn và bất biến của SHA256 content hash.
- **Hồi quy toàn bộ hệ thống:** 359/359 tests trong `openproject/ai/tests` đạt `PASS` (0 failed, 1 skipped).

---

## 3. Danh mục files thay đổi
- Tạo mới: `openproject/ai/gateway/knowledge_classifier.py`
- Tạo mới: `openproject/ai/tests/test_knowledge_classifier.py`
- Tạo mới: `docs/ai-multi-agent-upgrade/artifacts/P06-01-knowledge-classifier-acceptance.md`
