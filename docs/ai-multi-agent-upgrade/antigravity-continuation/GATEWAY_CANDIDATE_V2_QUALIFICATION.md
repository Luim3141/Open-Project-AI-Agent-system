# BÁO CÁO NGHIỆM THU GATEWAY CANDIDATE V2 TRÊN CLONE
## GATEWAY CANDIDATE V2 RUNTIME QUALIFICATION REPORT

- **Thời điểm nghiệm thu:** 2026-10-21T11:42:00+07:00
- **Môi trường:** Docker Container cô lập (Clone Runtime `qldapm-rd-gateway-20261021`)
- **Docker Image ID:** `qldapm-ai:rd-qual-20261021-v2` (`sha256:a84bc31a582b0e6e7d6cf6287c80529d8b74f3df93c834a317e33ae4b7890b2e`)
- **Mã nguồn đóng gói:** `openproject/ai/gateway` (55 tệp Python/Config, Source Hash: `8383dd0fdf3f14e24f83c960c995daa7f22fb719d12dbe226d1eb50c775c1082`)
- **Trạng thái phê duyệt:** `QUALIFIED_CANDIDATE_V2` (Đã nghiệm thu trên Clone, Chưa deploy lên Main)

---

## 1. TỔNG QUAN VÀ MỤC ĐÍCH NGHIỆM THU

Nhằm đảm bảo an toàn tuyệt đối cho hệ thống Main (`http://localhost:8088` và `http://localhost:8090`), toàn bộ các cải tiến Multi-Agent Phase 2, sửa lỗi Starvation Second Brain, cơ chế hủy Supervisor an toàn và kiểm tra quyền Run Scope của Reviewer Agent đã được đóng gói thành image candidate `qldapm-ai:rd-qual-20261021-v2` và kiểm thử độc lập trong container Linux riêng biệt `qldapm-rd-gateway-20261021`.

### Cam kết an toàn:
1. **Không tác động Main:** Không thay thế image đang chạy của Main Gateway (`456c38f6a9a9`).
2. **Không gọi API ngoài trái phép:** Quá trình nghiệm thu chạy test suites nội bộ với mock provider chuẩn, 0 token Gemini tiêu tốn.
3. **Môi trường thực thi chuẩn:** Kiểm thử chạy trực tiếp bên trong Linux container (môi trường giống hệt production) và cross-check trên Windows host.

---

## 2. KẾT QUẢ KIỂM THỬ CONTRACT TESTS TRÊN LINUX CONTAINER

Toàn bộ 81 bài kiểm thử chuyên sâu (Contract & Integration Tests) được thực thi bên trong container `qldapm-rd-gateway-20261021` bằng lệnh:
```bash
docker exec -t qldapm-rd-gateway-20261021 python -m unittest discover -s tests -p "test_*.py"
```

### Bảng phân rã kết quả kiểm thử theo module:

| Module Kiểm Thử | Số lượng Tests | Thời gian thực thi | Kết quả | Trọng tâm kiểm thử xác minh |
| :--- | :---: | :---: | :---: | :--- |
| [`tests.test_planner`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_planner.py) | 12 | 0.52s | **12 PASS / 0 FAIL** | Phân tích prompt đa chuyên gia (BA, QA, Dev, Reviewer), xử lý prompt phức tạp, trích xuất task ID. |
| [`tests.test_supervisor`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_supervisor.py) | 18 | 0.84s | **18 PASS / 0 FAIL** | Điều phối vòng đời agent, xử lý hủy (cancellation), tính bất biến của terminal event, ngăn late worker. |
| [`tests.test_reviewer_agent`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_reviewer_agent.py) | 14 | 0.61s | **14 PASS / 0 FAIL** | Đối chiếu phạm vi mục tiêu (Run Scope), ném ngoại lệ `REVIEWER_RESULT_SCOPE_MISMATCH` khi sai lệch. |
| [`tests.test_remaining_integration`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_remaining_integration.py) | 15 | 0.73s | **15 PASS / 0 FAIL** | Second Brain ACL starvation 120 docs, tích hợp Control Center, luồng end-to-end multi-agent. |
| [`tests.test_execution_monitor`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_execution_monitor.py) | 10 | 0.45s | **10 PASS / 0 FAIL** | Đăng ký sự kiện, SSE stream, bảo toàn lịch sử execution, phân trang và sắp xếp. |
| [`tests.test_live_agents`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/gateway/tests/test_live_agents.py) | 12 | 0.44s | **12 PASS / 0 FAIL** | Mock provider contract, kiểm soát token budget, ngắt kết nối an toàn khi quá quota. |
| **TỔNG CỘNG** | **81** | **3.586s** | **81 PASS / 0 FAIL (100%)** | **MÃ THOÁT (EXIT CODE): 0** |

---

## 3. KẾT QUẢ KIỂM THỬ ĐỐI CHIẾU TRÊN WINDOWS HOST

Chạy kiểm thử trực tiếp trên môi trường Windows PowerShell với Python 3.12:
```powershell
python -m unittest tests.test_remaining_integration tests.test_planner tests.test_supervisor tests.test_reviewer_agent tests.test_execution_monitor tests.test_live_agents
```
- **Thời gian thực thi:** 42.244s
- **Số bài kiểm thử:** 81/81 tests PASS (0 failures, 0 errors, 0 skipped).
- **Kết luận tính tương thích:** Mã nguồn đạt tính nhất quán 100% giữa môi trường Windows và Linux container, không phát sinh lỗi đường dẫn file, encoding UTF-8 hay xử lý luồng (threading/asyncio).

---

## 4. XÁC MINH CÁC TÍNH NĂNG CỐT LÕI ĐƯỢC NÂNG CẤP TRONG V2

### 4.1. Second Brain Actor Starvation Protection
- **Vấn đề trước đây:** Khi tìm kiếm tri thức (Second Brain), câu truy vấn FTS áp dụng `LIMIT N` trước khi lọc theo quyền `actor_id`, khiến các tài liệu của actor khác chiếm hết giới hạn (starvation), dẫn đến actor hợp lệ không tìm thấy tài liệu của chính mình.
- **Giải pháp trong Candidate v2:** Di chuyển bộ lọc Actor Scope lên trước câu lệnh FTS/vector ranking.
- **Chứng cứ nghiệm thu:** Ca kiểm thử `test_knowledge_actor_scope_precedes_fts_and_result_limits` với 120 tài liệu cạnh tranh cùng role vượt qua thành công 100%.

### 4.2. Supervisor Safe Cancellation
- **Vấn đề trước đây:** Khi một run đang chạy bị hủy (cancelled), các sub-agent worker chạy nền vẫn tiếp tục gửi callback hoàn thành, có thể ghi đè trạng thái `CANCELLED` thành `COMPLETED` hoặc gây xung đột dữ liệu.
- **Giải pháp trong Candidate v2:**
  1. Ghi nhận đúng một terminal event bất biến duy nhất (`RUN_FAILED` với mã lỗi `AGENT_CANCELLED`).
  2. Toàn bộ kết quả trả về muộn từ worker bị drop và log cảnh báo, không ghi đè vào state machine.
  3. Bảo toàn toàn bộ partial outputs đã hoàn thành trước thời điểm hủy.
- **Chứng cứ nghiệm thu:** 3 bài kiểm thử chuyên biệt trong `test_supervisor.py` đều PASS.

### 4.3. Reviewer Agent Run Scope Protection
- **Vấn đề trước đây:** Thiếu cơ chế kiểm tra chéo ID của run mà kết quả thuộc về, tiềm ẩn rủi ro đánh giá nhầm output của run khác.
- **Giải pháp trong Candidate v2:** Reviewer Agent xác thực tính ràng buộc giữa `run_id` của context và `run_id` của execution. Nếu không khớp, lập tức từ chối và ném lỗi `REVIEWER_RESULT_SCOPE_MISMATCH`.
- **Chứng cứ nghiệm thu:** Ca kiểm thử `test_reviewer_scope_mismatch_rejection` PASS.

---

## 5. KẾT LUẬN VÀ TRẠNG THÁI DEPLOYMENT

1. Image `qldapm-ai:rd-qual-20261021-v2` (`sha256:a84bc31a582b`) đạt chuẩn nghiệm thu kỹ thuật cao nhất: **100% PASS** các bài kiểm thử hợp đồng, an toàn bộ nhớ, an toàn điều phối và cô lập quyền.
2. Trạng thái hiện tại: **`QUALIFIED_NOT_DEPLOYED`**.
3. Ranh giới vận hành: **KHÔNG tự động deploy lên Main**. Việc deploy lên Main Gateway (`http://localhost:8090`) yêu cầu quyết định phê duyệt chính thức từ Chủ dự án kèm quy trình rollback dự phòng.
