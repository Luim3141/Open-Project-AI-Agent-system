# BÁO CÁO PHÂN LOẠI & KIỂM THỬ TÍCH HỢP THỰC TẾ (REAL_INTEGRATION_TEST_REPORT.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian thực hiện:** 2026-10-17T16:56:00+07:00  
**Tập lệnh kiểm thử:** `openproject/ai/run_full_regression.py` và các lệnh probe container trực tiếp.

---

## 1. PHÂN LOẠI CHI TIẾT 40 TEST SUITES TRONG BỘ KIỂM THỬ HỒI QUY

Để đảm bảo tính trung thực và không đánh tráo khái niệm giữa kiểm thử giả lập (mock) và kiểm thử thực tế (live integration), toàn bộ 40 test suites được phân loại rõ ràng:

| Nhóm Kiểm Thử | Số lượng Suite | Danh sách File Kiểm Thử | Bản chất kỹ thuật & Giá trị nghiệm thu |
|---|---|---|---|
| **Security & Threat Mitigation** | 4 | `test_rbac_cross_role_matrix.py`, `test_prompt_injection_and_secret_exfil.py`, `test_threat_model_operator_socket.py`, `test_proposal_aggregation.py` | Kiểm tra ma trận phân quyền PM-only-write, chống prompt injection, chống rò rỉ secret key, kiểm soát docker socket. **Đạt chuẩn bảo mật khắt khe.** |
| **Deterministic Intent & NLP Evals** | 1 | `test_intent_evals.py` | Benchmark 32 ca kiểm thử song ngữ (Anh/Việt), phân loại intent, phát hiện câu lệnh mơ hồ. **Đạt độ chính xác 100%.** |
| **Business Workflows & Reporting** | 9 | `test_daily_brief.py`, `test_weekly_report.py`, `test_workload_detector.py`, `test_sprint_readiness.py`, `test_qa_change_workflow.py`, `test_role_alerts.py`, `test_scheduler_timezone_and_ownership.py`, `test_sprint_report.py`, `test_local_queries.py` | Kiểm tra logic sinh báo cáo và cảnh báo không tiêu tốn token Gemini. Đảm bảo tính toán đúng số lượng task, blocker, DoR. |
| **Multi-Agent Contracts** | 7 | `test_planner.py`, `test_pm_agent.py`, `test_ba_agent.py`, `test_dev_agent.py`, `test_qa_agent.py`, `test_reviewer_agent.py`, `test_supervisor_5_actors.py` | Kiểm tra hợp đồng dữ liệu giữa 6 agent, cô lập ngữ cảnh giữa các role. Gọi thử nghiệm tối thiểu đến Google API (`test_pm_agent.py` trả về HTTP 200). |
| **Second Brain & Retrieval** | 6 | `test_knowledge_classifier.py`, `test_knowledge_storage.py`, `test_knowledge_search.py`, `test_knowledge_retrieval.py`, `test_knowledge_ingestion.py`, `test_knowledge_ui_answer.py` | Kiểm tra thuật toán băm SHA256 chunking, bộ lọc phân quyền dự án và truy xuất ngữ cảnh với 10 kịch bản golden. (Lưu ý: Storage hiện chạy in-memory trong module Python). |
| **Resilience & Fault Injection** | 3 | `test_fault_injection.py`, `test_workflow_pause.py`, `test_lan_devices_and_network_dropout.py` | Bơm lỗi giả lập HTTP 429, 503, rớt mạng, kiểm tra thuật toán exponential backoff và circuit breaker. |
| **Data Recovery & Persistence** | 3 | `test_backup_restore_drill.py`, `test_local_backup.py`, `test_backup_schedule.py` | Kiểm tra tính toàn vẹn snapshot SQLite WAL bằng lệnh `PRAGMA integrity_check` và khôi phục khóa n8n. |
| **API Contract & State** | 3 | `test_control_center.py`, `test_conversation_memory.py`, `test_decision_memory.py` | Kiểm tra API Control Center qua HTTP TestClient (Starlette/FastAPI), bộ nhớ hội thoại và lịch sử quyết định có băm nguồn gốc. |
| **n8n Automation Engine** | 2 | `test_n8n_owner.py`, `test_n8n_outage_policy.py` | Kiểm tra xác thực khóa chữ ký HMAC và chính sách phục hồi sau sự cố n8n. |
| **Capacity & Synthetic Acceptance** | 2 | `test_concurrent_load_20_users.py`, `test_p10_docker_and_lan_acceptance.py` | Kiểm thử đa luồng với MockNativeLoad. *(Phần năng lực 20 user thật được hoãn theo quyết định của Chủ dự án).* |

---

## 2. KẾT QUẢ KIỂM THỬ TRỰC TIẾP TRÊN RUNTIME CONTAINER (LIVE VERIFICATION)

Ngoài việc chạy 40 test suites tự động, kiểm toán viên đã thực thi các lệnh kiểm tra trực tiếp trên các container Docker đang hoạt động:

1. **AI Gateway Live Health (127.0.0.1:18092):**
   - Lệnh: `GET http://127.0.0.1:18092/health`
   - Phản hồi: `{"status":"ok"}` (HTTP 200).
2. **OpenProject Staging Web Live Health (127.0.0.1:18091):**
   - Lệnh: `GET http://127.0.0.1:18091/health_checks/default`
   - Phản hồi: `default: PASSED Application is running (0.000s)` (HTTP 200).
3. **n8n Community Editor Live Ports (127.0.0.1:18090 & 127.0.0.1:5678):**
   - Cả 2 cổng đều phản hồi HTTP 200 trên loopback nội bộ; hoàn toàn không lộ ra mạng ngoài.
4. **PostgreSQL Staging Database Query:**
   - Đã kết nối trực tiếp vào `qldapm-ai-stage-db-1`:
   - Xác nhận dự án ID 3: `QLDAPM — Local Community` (`qldapm-local`).
   - Xác nhận 5 vai trò tùy chỉnh: `QLDAPM PM`, `QLDAPM BA-PM`, `QLDAPM BE`, `QLDAPM FE`, `QLDAPM QA`.
5. **n8n Container Workflow Export:**
   - Lệnh: `docker exec -i qldapm-ai-stage-n8n-1 n8n export:workflow --all`
   - Xác nhận 3 workflows n8n được nạp thật trong container, trong đó `qldapmDailyBrief` và `qldapmWorkflowErrors` đang ở trạng thái `active: true`.
