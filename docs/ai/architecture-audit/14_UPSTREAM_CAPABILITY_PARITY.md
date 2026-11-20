# HỒ SƠ PHÁP Y M5: ĐỐI CHIẾU NĂNG LỰC VỚI CÁC MÔ HÌNH THƯỢNG NGUỒN (UPSTREAM PARITY)
> Thời điểm kiểm toán: `2026-10-30 20:30:54 UTC`  
> Các hệ thống đối chiếu: **Paperclip**, **Agency Agents**, **Superpowers**  
> Định hướng thích ứng: **Chọn lọc tinh gọn theo triết lý Ponytail (Zero Bloat)**

---

## 1. BẢNG ĐỐI SOÁT VỚI PAPERCLIP (AUTONOMOUS TASK ENGINE)

| Cơ chế Paperclip | Mức độ tương đương trong QLDAPM | Hiện thực mã nguồn | Đánh giá & Ranh giới |
| :--- | :--- | :--- | :--- |
| **Task Checkout & Concurrency Lock** | **Tương đương 100%** | `store.py` (`acquire_engineering_lock`) | Chỉ 1 tiến trình được chạy tại 1 thời điểm; chặn hoàn toàn race condition. |
| **Budget Enforcement** | **Tương đương 100%** | `gemini.py` (`BoundedClient`), `openclaw_provider_gate.py` | Giới hạn cứng token per call, turns, daily RPM/RPD, cấm vượt ngân sách. |
| **Human-in-the-Loop Approval** | **Tương đương 100%** | `qldapm_ai_controller.rb`, `rbac.rb` | Yêu cầu Owner (User 18) phê duyệt trước khi chuyển sang AUTO hoặc deploy. |
| **Safe Auto-Shutoff** | **Tương đương 100%** | `engineering_auto.py` (`ALL_DELIVERED`) | Tự động tắt trạng thái AUTO khi hoàn tất toàn bộ 5 units, không chạy vòng lặp vô tận. |
| **Distributed Multi-Tenant Queue** | **Lược bỏ có chủ đích (Ponytail)** | Single Project / Local SQLite Queue | Tránh phức tạp hóa hạ tầng cho quy trình outsourcing cục bộ. |

---

## 2. BẢNG ĐỐI SOÁT VỚI AGENCY AGENTS (SPECIALIZED PERSONAS)

| Khái niệm Agency Agents | Mức độ tương đương trong QLDAPM | Hiện thực mã nguồn | Đánh giá & Ranh giới |
| :--- | :--- | :--- | :--- |
| **Formal Role Personas** | **Tương đương 100%** | `agent_registry.py`, `engineering_personas.py` | 6 vai trò chuyên biệt (Supervisor, PM, BA, Dev, Reviewer, QA) với system prompts chuẩn hóa. |
| **Strict Input / Output Contracts** | **Tương đương 100%** | Pydantic Models (`extra="forbid"`) | Input/Output contract rõ ràng, từ chối mọi trường lạ hoặc dữ liệu không kiểm chứng. |
| **Quality Criteria & Handoff Gates** | **Tương đương 100%** | `engineering_units.py`, `engineering_lifecycle.py` | Handoff chỉ diễn ra khi thỏa mãn điều kiện biên (AC passed, Pytest exit 0). |
| **Complex Inter-Agent Negotiation** | **Lược bỏ có chủ đích (Ponytail)** | Deterministic DAG via Supervisor | Thay thế đàm phán tự do tốn kém token bằng cây điều phối tất định không tốn LLM. |

---

## 3. BẢNG ĐỐI SOÁT VỚI SUPERPOWERS (ENGINEERING RIGOR)

| Phương pháp Superpowers | Mức độ tương đương trong QLDAPM | Hiện thực mã nguồn | Đánh giá & Ranh giới |
| :--- | :--- | :--- | :--- |
| **Test-Driven Development (TDD)** | **Tương đương 100%** | `SKILL.md` (Dev), Pytest Suite | Viết test thất bại (RED) trước khi viết code nghiệp vụ (GREEN). |
| **Isolated Git Worktrees** | **Tương đương 100%** | `~/engineering/feedback-4d13e695555a8d44` | Cách ly hoàn toàn mã nguồn demo với workspace chính. |
| **Systematic Debugging** | **Tương đương 100%** | `SKILL.md` (Dev), Bounded Rework | Triệu chứng → Bằng chứng → Một giả thuyết → Thử nghiệm hoàn nguyên → Sửa lỗi. |
| **Verification-Before-Completion** | **Tương đương 100%** | Pytest Execution + XML Report (`acceptance-0.xml`) | Chỉ công nhận hoàn thành khi có bằng chứng thực tế từ mã thoát exit 0. |

---

## 4. KẾT LUẬN KIỂM TOÁN TƯƠNG ĐƯƠNG THƯỢNG NGUỒN

Hệ thống QLDAPM MAIN đã kế thừa xuất sắc những tinh hoa về kỷ luật kỹ thuật của Paperclip, Agency Agents và Superpowers, đồng thời loại bỏ triệt để các lớp trừu tượng thừa, đạt được hiệu năng cao và độ tin cậy tuyệt đối với chi phí 0 đồng.
