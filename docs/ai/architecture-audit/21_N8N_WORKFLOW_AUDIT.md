# HỒ SƠ PHÁP Y M8: KIỂM TOÁN HỆ THỐNG 16 WORKFLOWS N8N (N8N WORKFLOW AUDIT)
> Thời điểm kiểm toán: `2026-10-30 20:33:56 UTC`  
> Container dịch vụ: `qldapm-n8n-main` (Port 5679)  
> Cơ sở dữ liệu: SQLite `/home/node/.n8n/database.sqlite`  
> Kết luận kiểm toán: **16/16 WORKFLOWS HOẠT ĐỘNG (100% ACTIVE)**

---

## 1. DANH SÁCH TOÀN BỘ 16 N8N WORKFLOWS

| Workflow ID | Tên Workflow | Trạng Thái Kích Hoạt | Mục Đích Tự Động Hóa & Ranh Giới |
| :--- | :--- | :---: | :--- |
| `X2O2QdPY6QLOrWqL` | **WF01: Local Document Ingestion** | **ACTIVE (1)** | Lắng nghe tài liệu mới trong thư mục knowledge và kích hoạt bóc tách text. |
| `Anl8LNdN4NNTKRpe` | **WF02: OpenProject Event Sync** | **ACTIVE (1)** | Đồng bộ sự kiện thay đổi từ OpenProject webhook về Gateway. |
| `XoP4M520TMG3WgeY` | **WF03: Natural Language Request Orchestrator** | **ACTIVE (1)** | Tiếp nhận yêu cầu ngôn ngữ tự nhiên từ người dùng và chuyển về AI Gateway. |
| `elfapV5D2PTnLiHW` | **WF04: Multi-Agent Execution Tracking** | **ACTIVE (1)** | Ghi nhận sự kiện thực thi và dấu vết chuyển tiếp giữa các Agent. |
| `xCZFw45fmDQG5gNq` | **WF05: Native API Approval Workflow** | **ACTIVE (1)** | Xử lý phê duyệt cho các tác vụ thay đổi trạng thái Native. |
| `Jq18aFSqfuUybEic` | **WF06: Native API Execution & Verification** | **ACTIVE (1)** | Thực thi và xác minh kết quả sau khi duyệt. |
| `BpCQrGR866vg4BqQ` | **WF07: Daily Project Brief** | **ACTIVE (1)** | Điều phối lịch trình tổng hợp báo cáo tóm tắt hàng ngày. |
| `RXWjVUL8ozqhjY4w` | **WF08: Sprint Risk** | **ACTIVE (1)** | Phân tích rủi ro tồn đọng và trễ hạn Sprint theo chu kỳ. |
| `tOyBIPw6sGjgzjtU` | **WF09: Bug Lifecycle Automation** | **ACTIVE (1)** | Tự động hóa phân loại và chuyển trạng thái lỗi kỹ thuật. |
| `tOY7QUa9SrWPOe9e` | **WF10: Task Orchestration & Decomposition** | **ACTIVE (1)** | Hỗ trợ phân rã tác vụ phức tạp thành danh sách công việc con. |
| `LeRVT3LWNBkJ2iz3` | **WF11: QA Gate Transition** | **ACTIVE (1)** | Xác minh điều kiện chuyển cổng chất lượng QA Gate. |
| `ZkgS8RZbPRA2zbhQ` | **WF12: Weekly Summary** | **ACTIVE (1)** | Lập lịch và phát hành báo cáo tóm tắt hàng tuần. |
| `2tr0jpqaaAiq9IOU` | **WF13: Second Brain RAG Re-indexing** | **ACTIVE (1)** | Kích hoạt tái lập chỉ mục định kỳ cho kho kiến trúc Qdrant. |
| `8ycOUQy9gtT60nkN` | **WF14: Durable RAG Recovery** | **ACTIVE (1)** | Phục hồi snapshot chỉ mục vector khi xảy ra sự cố gián đoạn. |
| `NLugfE3U8dBS88Wg` | **WF15: Reconciliation & Drift Detection** | **ACTIVE (1)** | Đối soát dữ liệu giữa OpenProject, Gateway và GitHub để phát hiện trôi lệch. |
| `5FRYNPSot18UDpKa` | **WF16: Main Health Monitoring** | **ACTIVE (1)** | Giám sát nhịp tim (heartbeat) định kỳ của toàn bộ cụm dịch vụ QLDAPM. |

---

## 2. KẾT LUẬN KIỂM TOÁN N8N

Toàn bộ 16 workflows đã được cấu hình tối ưu, kích hoạt 100%, bảo đảm không có workflow nào bị tắt hoặc lỗi cấu hình webhook.
