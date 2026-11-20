# BÁO CÁO ĐỒNG BỘ NGUỒN VÀ MÔI TRƯỜNG TRIỂN KHAI (DEPLOYMENT & SOURCE CODE PARITY)

> **Tài liệu:** `08_DEPLOYMENT_SOURCE_PARITY.md`  
> **Dự án:** QLDAPM MAIN  
> **Phiên bản Docker Deployment:** `continuation-r24-20261031`  
> **Ngày xác nhận:** 31/10/2026  
> **Đánh giá tổng thể:** 100% ĐỒNG BỘ GIỮA MÃ NGUỒN HOST, CONTAINER, WSL2 VÀ GITHUB REMOTE.

---

## 1. MA TRẬN ĐỒNG BỘ PHIÊN BẢN CÁC THÀNH PHẦN

| Phân hệ / Vị trí | Phiên bản / Tag / Branch | Trạng thái đồng bộ | Bằng chứng xác minh |
| :--- | :--- | :--- | :--- |
| **OpenProject Rails Core** | `qldapm-core:engineering-continuation-r24-20261031` | `SYNCHRONIZED` | Chứa `qldapm_ai_controller.rb` đã sửa route executions/runs và mở rộng knowledge search |
| **QLDAPM AI Gateway** | `qldapm-ai:engineering-continuation-r24-20261031` | `SYNCHRONIZED` | Chứa `knowledge_search.py` đã bỏ logic xóa lexical BM25 khi dense rỗng |
| **n8n Automation Main** | `n8n:2.43.6` (Port 5679) | `SYNCHRONIZED` | Chứa đủ 16/16 workflows tự động hóa |
| **OpenClaw WSL2 Worktree** | `/home/openclaw/engineering/feedback-bb9a628fe5b7be67` | `SYNCHRONIZED` | Branch `codex/openclaw-feedback-bb9a628fe5b7be67`, Commit `0498ceed...` |
| **Local Demo Repository** | `D:\AI project\QLDAPM-demo\mini-task-manager` | `SYNCHRONIZED` | Đã fetch branch `origin/codex/openclaw-feedback-bb9a628fe5b7be67` từ GitHub |
| **Remote GitHub Repo** | `Luim3141/mini-task-manager` | `SYNCHRONIZED` | Commit `0498ceed...` đã được push thành công lên PR #6 |

---

## 2. KIỂM TOÁN TÍNH NGUYÊN VẸN CỦA GIT REPOSITORY

### 2.1. Kiểm tra Workspace chính (`D:\AI project\QLDAPM chat`)
- Không có bất kỳ thay đổi nào làm phá vỡ cấu trúc Rails engine hoặc AI Gateway.
- Thư mục bằng chứng `docs/ai/engineering/runs/` lưu trữ đầy đủ 6 runs lịch sử với đầy đủ các tệp bằng chứng (`claim-latest.json`, `delivery-steps.json`, `result.json`, `candidate-0.diff`, `dev-0-result.json`, `review-0-result.json`, `qa-0-result.json`, `acceptance-0.xml`).

### 2.2. Kiểm tra Demo Repository (`D:\AI project\QLDAPM-demo\mini-task-manager`)
- Nhánh cơ sở: `codex/mini-task-manager-ready`.
- Các nhánh chức năng độc lập:
  - `origin/codex/openclaw-create-list-persistence-v1` -> Đã merge vào `main` (PR #1).
  - `origin/codex/openclaw-crud-search-web-v1` -> Đã merge vào `main` (PR #2).
  - `origin/codex/openclaw-feedback-283138e910432528` -> Đang mở (PR #3).
  - `origin/codex/openclaw-feedback-4d13e695555a8d44` -> Đang mở (PR #4).
  - `origin/codex/openclaw-health-check-v1` -> Đang mở (PR #5).
  - `origin/codex/openclaw-feedback-bb9a628fe5b7be67` -> Đang mở (PR #6).

---

## 3. BẢO VỆ PHẠM VI SẢN XUẤT (PRODUCTION SCOPE INVARIANCE)

- **Work Packages Project 5:** Không có bất kỳ nhánh hay tiến trình nào thực hiện thao tác ghi đè, xóa hoặc sửa đổi dữ liệu của Project 5.
- **Tính toán Diff tối giản (Senior Dev Mode):**
  - Diff tính năng `GET /tasks/summary` chỉ gồm 36 dòng mã nguồn sạch, không import thư viện thừa, không tạo wrapper hay lớp trừu tượng không cần thiết, tái sử dụng 100% các helper và kết nối SQLite có sẵn.
