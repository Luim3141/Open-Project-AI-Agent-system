# Open Project AI Agent System

Hệ thống quản lý dự án local dựa trên OpenProject Community, bổ sung AI Gateway, Agent Studio, Telegram Commander, n8n automation và các công cụ vận hành Jira.

Repository này là **bản source đã lọc thông tin nhạy cảm ngày 20/11/2026**. Các báo cáo nghiệm thu trong `docs/` là bằng chứng lịch sử có phạm vi riêng, không phải cam kết mọi tính năng đều hoạt động trên một máy mới.

## Thành phần

| Đường dẫn | Nội dung |
| --- | --- |
| `openproject/` | Docker Compose, quản lý OpenProject và upstream lock |
| `openproject/ai/gateway/` | AI Gateway, phân quyền, agent, đề xuất và audit |
| `openproject/ai/core/overlay/` | Source Rails tùy biến được chép vào image OpenProject |
| `openproject/ai/core/agent-studio-v2/` | Frontend React và tests của Agent Studio |
| `openproject/ai/telegram-ai/` | Telegram Commander và tests |
| `openproject/ai/automation/`, `automation/` | Workflow và công cụ automation |
| `openproject/development-patch/` | Biến thể development, khác overlay, có provenance |
| `forge/`, `jira-bot/`, `tools/` | Tích hợp Jira, Forge và công cụ quản trị |
| `tests/`, `openproject/ai/tests/` | Unit, integration và các harness vận hành |
| `docs/`, `architecture.md`, `CONTEXT.md` | Thiết kế, thuật ngữ, runbook và báo cáo |

## Bắt đầu

Môi trường triển khai chính: Windows, PowerShell, Docker Desktop với Linux containers/WSL2, Git và Python. Unit tests dùng Python 3.12 trong CI; frontend dùng Node.js 22.

```powershell
git clone https://github.com/Luim3141/Open-Project-AI-Agent-system.git
Set-Location Open-Project-AI-Agent-system
python scripts/check_publication.py
```

Đọc [hướng dẫn cài đặt](docs/GETTING_STARTED.md) trước khi chạy Setup. Source clone không bao gồm database, tài khoản, API keys hay runtime của máy tác giả. Không có mật khẩu mặc định công khai. Các harness live đã bỏ credentials phải được cấu hình lại riêng; không dùng marker `PUBLICATION_REDACTED` làm credential.

## Kiểm tra offline

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r openproject/ai/requirements.lock.txt
$env:PYTHONPATH = 'openproject/ai'
.\.venv\Scripts\python.exe -m unittest discover -s openproject/ai/tests -p test_agent_observer.py
Set-Location openproject/ai/core/agent-studio-v2
npm ci
npm test
npm run build
```

Lệnh `pip install`/`npm ci` tải dependencies; tự kiểm nguồn và quyền sử dụng trước khi triển khai. CI chỉ chạy các suite offline chọn lọc. Nhiều file mang tên `test_*` là harness có thể gọi Docker, Jira, GitHub, Telegram hoặc model thật; **không chạy toàn bộ discovery trên môi trường production**.

Publication checker đọc **Git index**, tức file đã commit hoặc đã stage. Sau khi sửa, stage đúng các file đã xem rồi chạy checker; file mới chưa stage không nằm trong kiểm tra.

## Tài liệu

- [Kiến trúc](architecture.md), [domain model](CONTEXT.md).
- [OpenProject local](openproject/README.md), [AI README](openproject/ai/README.md), [AI checkpoint](openproject/ai/CHECKPOINT.md).
- [AI operations](openproject/ai/README_OPERATIONS.md), [Telegram](openproject/ai/telegram-ai/README.md).
- [Đóng góp](CONTRIBUTING.md), [bảo mật](SECURITY.md), [giấy phép và upstream](THIRD_PARTY_NOTICES.md).
- [Phạm vi xuất bản và giới hạn](docs/publication/README.md).

Một số liên kết tuyệt đối Windows và liên kết tới ảnh/bằng chứng private trong tài liệu cũ chỉ dùng được ở workspace gốc. Ưu tiên hướng dẫn tương đối trong README này cho clone mới.

## Giới hạn vận hành

Không bật automation ghi dữ liệu, auto-deploy, auto-merge hay gọi model khi chưa có cấu hình, phạm vi và phê duyệt tương ứng. Giữ mặc định an toàn, không mua add-on/trial. Đặc biệt, RAG có các gate lịch sử chưa đạt; đọc báo cáo theo timestamp và phạm vi, không suy ra production-ready từ việc source đã lên GitHub.
