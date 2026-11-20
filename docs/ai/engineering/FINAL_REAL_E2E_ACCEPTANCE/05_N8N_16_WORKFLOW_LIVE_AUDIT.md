# BÁO CÁO KIỂM TOÁN THỰC TẾ 16 QUY TRÌNH N8N AUTOMATION (PORT 5679)

> **Tài liệu:** `05_N8N_16_WORKFLOW_LIVE_AUDIT.md`  
> **Cổng truy cập chính thức:** `http://127.0.0.1:5679` (Container: `qldapm-n8n-main`)  
> **Phiên bản n8n:** 2.43.6  
> **Ngày kiểm toán:** 31/10/2026  
> **Tổng số workflow:** 16/16 ĐANG HOẠT ĐỘNG (ACTIVE).

---

## 1. DANH SÁCH VÀ TRẠNG THÁI 16 WORKFLOWS

| Mã quy trình | ID nội bộ n8n | Tên đầy đủ của Workflow | Loại Trigger | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **WF01** | `X2O2QdPY6QLOrWqL` | WF01: Local Document Ingestion | Webhook / File Watcher | `ACTIVE` |
| **WF02** | `Anl8LNdN4NNTKRpe` | WF02: OpenProject Event Sync | Webhook từ OpenProject | `ACTIVE` |
| **WF03** | `XoP4M520TMG3WgeY` | WF03: Natural Language Request Orchestrator | Webhook / Chatbot Intake | `ACTIVE` |
| **WF04** | `elfapV5D2PTnLiHW` | WF04: Multi-Agent Execution Tracking | Scheduled (1 ph) / Event | `ACTIVE` |
| **WF05** | `xCZFw45fmDQG5gNq` | WF05: Native API Approval Workflow | Webhook phê duyệt | `ACTIVE` |
| **WF06** | `Jq18aFSqfuUybEic` | WF06: Native API Execution & Verification | Event sau phê duyệt | `ACTIVE` |
| **WF07** | `BpCQrGR866vg4BqQ` | WF07: Daily Project Brief | Cron (08:00 AM hàng ngày) | `ACTIVE` |
| **WF08** | `RXWjVUL8ozqhjY4w` | WF08: Sprint Risk | Cron (12:00 PM hàng ngày) | `ACTIVE` |
| **WF09** | `tOyBIPw6sGjgzjtU` | WF09: Bug Lifecycle Automation | Webhook lỗi mới từ QA | `ACTIVE` |
| **WF10** | `tOY7QUa9SrWPOe9e` | WF10: Task Orchestration & Decomposition | Webhook tạo Work Package | `ACTIVE` |
| **WF11** | `LeRVT3LWNBkJ2iz3` | WF11: QA Gate Transition | Webhook cập nhật PR/Commit | `ACTIVE` |
| **WF12** | `ZkgS8RZbPRA2zbhQ` | WF12: Weekly Summary | Cron (Chủ nhật 18:00) | `ACTIVE` |
| **WF13** | `2tr0jpqaaAiq9IOU` | WF13: Second Brain RAG Re-indexing | Event sau khi task deliver | `ACTIVE` |
| **WF14** | `8ycOUQy9gtT60nkN` | WF14: Durable RAG Recovery | Scheduled (5 ph) / Retry | `ACTIVE` |
| **WF15** | `NLugfE3U8dBS88Wg` | WF15: Reconciliation & Drift Detection | Scheduled (15 ph) | `ACTIVE` |
| **WF16** | `5FRYNPSot18UDpKa` | WF16: Main Health Monitoring | Cron (Mỗi 5 phút) | `ACTIVE` |

---

## 2. KIỂM TOÁN TỪNG NHÓM CHỨC NĂNG TỰ ĐỘNG HÓA

### 2.1. Nhóm Thu nạp & Đồng bộ Dữ liệu (WF01, WF02, WF13, WF14)
- **Mục tiêu:** Đảm bảo mọi thay đổi từ tài liệu local, sự kiện OpenProject hoặc kết quả hoàn thành task kỹ thuật đều được đưa vào cơ sở tri thức Second Brain RAG mà không bị thất thoát.
- **Cơ chế chịu lỗi:** WF14 tự động quét các tác vụ chưa được vector index hoặc thất bại do mạng để tái thực thi theo cơ chế exponential backoff.

### 2.2. Nhóm Điều phối & Phân rã Yêu cầu (WF03, WF10)
- **Mục tiêu:** Tiếp nhận câu lệnh ngôn ngữ tự nhiên từ người dùng, kích hoạt các Agent phân tích ngữ nghĩa, chia nhỏ thành các User Stories, Tasks và gán phụ thuộc logic vào OpenProject.

### 2.3. Nhóm Quản trị Rủi ro & Phê duyệt An toàn (WF05, WF06)
- **Mục tiêu:** Bảo vệ các thao tác ghi phá hủy (destructive operations). Mọi thay đổi về workflow, xóa dự án hoặc deploy production đều phải qua cổng kiểm soát phê duyệt an toàn.

### 2.4. Nhóm Báo cáo & Giám sát Hệ thống (WF07, WF08, WF12, WF16)
- **Mục tiêu:** Tự động tạo tóm tắt hàng ngày, cảnh báo nguy cơ chậm tiến độ sprint, tổng kết hiệu suất theo tuần và liên tục giám sát trạng thái của tất cả các container.
- **Kênh thông báo:** Tích hợp trực tiếp vào OpenProject Activities, webhook thông báo local và bảng điều khiển Command Center.
