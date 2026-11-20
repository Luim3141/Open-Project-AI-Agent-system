# P05-01 accepted — 17Oct2026

Chọn orchestration tối giản: LangGraph nếu tương thích, nếu không typed state machine nội bộ.

## 1. Tóm tắt kết quả
- Hoàn thành tài liệu Quyết định Kiến trúc [ADR-0003: Lựa chọn Orchestration tối giản: Typed State Machine nội bộ thay vì LangGraph](file:///d:/AI%20project/QLDAPM%20chat/docs/adr/0003-orchestration-typed-state-machine.md).
- Quyết định: **Chọn Typed State Machine nội bộ**, từ chối LangGraph.
- Lý do kỹ thuật cốt lõi:
  1. *Zero Dependency Bloat (Triết lý Ponytail)*: LangGraph làm tăng image size 150–300MB, kéo theo nhiều transitive dependencies có nguy cơ xung đột với `google.genai` SDK và `starlette`/`httpx`. Trong khi đó, Typed State Machine sử dụng 100% stack hiện có (`pydantic` v2 strict, Python stdlib `enum`, `typing`, `sqlite3`), 0 dependency mới.
  2. *Bảo vệ Quota Free Tier (15 RPM / 500 RPD)*: LangGraph có các vòng lặp ẩn (reflection/retry loops) dễ làm thất thoát token và cạn kiệt hạn mức 500 RPD của 5 users. Typed State Machine bảo đảm kiểm tra hạn mức qua `check_rpm()` và bảng `gemini_usage` trước từng lần gọi provider.
  3. *Tương thích Native RBAC & PM-only-write*: Tích hợp trực tiếp với 5 actor IDs (6, 7, 8, 9, 10), chốt chặn phê duyệt của PM và cơ chế consent preview native mà không cần qua các layer trừu tượng phức tạp.
  4. *Lưu trữ bền vững (Persistence)*: Tận dụng trực tiếp `Store` SQLite hiện có với WAL mode và bảng `agent_tasks`, `agent_runs`, không cần thêm LangGraph Checkpointer trùng lặp.
- **Không thay đổi Gateway hay SDK đang hoạt động vô cớ**: Giữ nguyên image Gateway `006b9c6c...` và Core `8a42c7ef...`, giữ nguyên 7/7 containers staging `healthy`.

## 2. Bằng chứng kiểm thử và thẩm định (Evidence)
- **Tài liệu ADR**: [docs/adr/0003-orchestration-typed-state-machine.md](file:///d:/AI%20project/QLDAPM%20chat/docs/adr/0003-orchestration-typed-state-machine.md) (đã commit nội dung đầy đủ).
- **Kiểm thử đơn vị Agent Models & State Machine**:
  - `test_agent_models.py` + `test_agent_trace.py`: 10/10 tests PASS (1.554s).
  - `test_agent_api.py` + `test_agent_queue.py` + `test_agent_states.py` + `test_agent_store.py`: 24/24 tests PASS (8.474s).
  - Tổng cộng 34/34 tests kiểm chứng hợp đồng Agent Contract, transition states (`QUEUED`, `RUNNING`, `WAITING_QUOTA`, `WAITING_PROVIDER`, `BLOCKED_KEY_OR_MODEL`, `REVIEW`, `FAILED`, `COMPLETED`), pagination, ACL isolation và trace events đạt 100% PASS.
- **Bảo toàn dữ liệu & runtime**:
  - 7/7 containers staging `Up` và `(healthy)`.
  - Database OpenProject 221 tables nguyên vẹn.
  - Bảng `gemini_usage` giữ nguyên 471 records (0 provider calls phát sinh).
  - Môi trường main (8088/8090) không thay đổi.

## 3. Trạng thái task
- Task P05-01: **DONE**
- Tiến độ Phase P05: **1/12 tasks DONE (8.3%)**
- Tiến độ tổng: **56/113 tasks DONE (49.6%)**
- Bước kế tiếp: Task P05-02 (Supervisor planner: tách đọc vs ghi, xác định dependencies và budget trước gọi model).
