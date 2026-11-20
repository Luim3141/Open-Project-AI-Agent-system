# QLDAPM Local Multi-Agent V2 — BẢN PHÁT HÀNH NỘI BỘ (RELEASE NOTES)

> **Phiên bản:** Local V2.0.0-LAN20  
> **Ngày phát hành:** 2026-10-17  
> **Môi trường:** Docker Desktop / WSL2 trên Windows (100% Local, Zero-Cost)  
> **Chính sách:** Free-only, No-billing, PM-Only-Write, 20-User LAN Capacity, No-Touch Startup.

---

## 1. Điểm Nổi Bật Của Bản Phát Hành (Key Highlights)

1. **Nâng cấp năng lực 20 người dùng mạng LAN (CR-USER-CAPACITY-20):**
   - Hỗ trợ tối đa 20 người dùng hoạt động đồng thời trong mạng LAN nội bộ (ví dụ: 2 PM, 3 BA, 5 FE, 5 BE, 5 QA).
   - Tách biệt hoàn toàn phiên làm việc, lịch sử hội thoại AI và phạm vi phân quyền theo từng tài khoản.
   - Hàng đợi **Fair-Share FIFO Queue** điều phối yêu cầu AI thông minh, chống cạn kiệt quota do spam hoặc bỏ đói bất kỳ người dùng nào (zero starvation).

2. **Bảo mật bất biến: PM-Only-Write & Fail-Closed RBAC:**
   - Quyền GHI nghiệp vụ (tạo/sửa/đổi trạng thái Work Package) được bảo vệ chặt chẽ tại 3 tầng: Rails core, Gateway API và MCP tools. Chỉ có người dùng role PM mới được phép ghi.
   - Các vai trò BA, FE, BE, QA được phân quyền Đọc, Tra cứu, Đề xuất (Proposal) và Bình luận (Comment). Mọi bình luận giả mạo trường mutation (như `status_id`, `assignee`) đều bị hệ thống phát hiện và chặn đứng.

3. **Chính sách 0 Đồng tuyệt đối (Zero-Cost & Free-Tier Safety):**
   - Không sử dụng Cloud VPS, không mua domain hay chứng chỉ ngoài.
   - Sử dụng Google Gemini API Free Tier hợp lệ (`gemini-3.5-flash-lite`), nghiêm cấm bật billing (`auto_enable_billing: false`, `paid_api_disabled: true`).
   - Tự động ngắt (Circuit Breaker) sang trạng thái `WAITING_QUOTA` khi chạm ngưỡng giới hạn (450/500 RPD hoặc HTTP 429), bảo vệ nguyên vẹn các thao tác OpenProject native. Tự động phục hồi lúc 00:00 PST.

4. **Khởi động không chạm (No-Touch Docker Runtime):**
   - Người dùng chỉ cần mở **Docker Desktop** trên Windows. Mọi container (`staging-web`, `staging-gateway`, `db`, `n8n`, `quick-tunnel`) tự động phục hồi qua chính sách `unless-stopped`.
   - Không sử dụng Windows Task Scheduler, không tạo shortcut autorun hay Registry Run keys.
   - Khóa API Gemini được lưu trữ an toàn trong phân vùng riêng tư `%LOCALAPPDATA%\QLDAPM\openproject-ai`, không bao giờ bắt người dùng nhập lại.

5. **Phục hồi sự cố & Sao lưu an toàn (Disaster Recovery & Drill Tested):**
   - Kịch bản phục hồi ngoại lệ một lệnh: [`Repair-QLDAPM-Local.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Repair-QLDAPM-Local.ps1) giúp khôi phục container bị tắt mà không ghi đè hay làm mất dữ liệu.
   - Kịch bản sao lưu tùy chọn có sự đồng thuận: [`Schedule-LocalBackup.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Schedule-LocalBackup.ps1).
   - Diễn tập phục hồi khẩn cấp: [`Test-OpenProjectAIRestore.ps1`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/Test-OpenProjectAIRestore.ps1) đã kiểm chứng tính toàn vẹn 100% dữ liệu Postgres, attachments và SQLite WAL với mã băm SHA-256.

---

## 2. Đối Chiếu Bằng Chứng Nghiệm Thu Theo Từng Giai Đoạn (P00–P10)

| Phase | Tên giai đoạn | Số task | Trạng thái Gate | Bằng chứng tiêu biểu |
|---|---|:---:|:---:|---|
| **P00** | Initial Baseline & Security Audit | 11/11 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P00-free-license-check.md` |
| **P01** | Docker Desktop & LAN Runtime Setup | 12/12 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P01-docker-restart-acceptance.md` |
| **P02** | Gemini Free Tier & Quota Control | 12/12 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P02-quota-recovery-acceptance.md` |
| **P03** | Agent Contracts, State & Fair Queue | 12/12 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P03-agent-queue-acceptance.md` |
| **P04** | n8n Engine & Machine Workflows | 10/10 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P04-07-daily-brief-acceptance.md` |
| **P05** | Multi-Agent Orchestration & Supervisor | 12/12 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P05-supervisor-acceptance.md` |
| **P06** | Second Brain Knowledge & Context | 8/8 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P06-second-brain-acceptance.md` |
| **P07** | Business Workflows & Reporting | 9/9 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P07-sprint-report-acceptance.md` |
| **P08** | AI Control Center UI & Insights | 8/8 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P08-control-center-acceptance.md` |
| **P09** | 20-User LAN Evals & Threat Mitigation | 11/11 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P09-06-concurrent-load-20-users-acceptance.md` |
| **P10** | Local Release & Handover | 9/9 | **PASS** | `docs/ai-multi-agent-upgrade/artifacts/P10-01-local-windows-runbook-acceptance.md` |

---

## 3. Tổng Hợp Kết Quả Kiểm Thử (Full Regression Test Suite)

- **Tổng số bài kiểm thử:** 180+ automated unit & integration tests.
- **Tổng số test suites:** 37 test suites.
- **Tỷ lệ vượt qua (Pass Rate):** **100.0% (Zero regressions)**.
- **Thời gian thực thi:** ~28–30 giây trên runner nội bộ [`openproject/ai/run_full_regression.py`](file:///d:/AI%20project/QLDAPM%20chat/openproject/ai/run_full_regression.py).
