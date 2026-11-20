# Domain docs

Single-context: một `CONTEXT.md` và `docs/adr/` ở root. Đọc trước khi khám phá code; nếu chưa có, tiếp tục, không tạo tài liệu rỗng. Dùng vocabulary của glossary; nêu rõ nếu đề xuất trái một ADR hiện hành.

Nguồn hiện có: `architecture.md` phân biệt kiến trúc sản phẩm đề xuất và triển khai tracker thực; `jira-workflows.md` định nghĩa Epic/Task/Subtask, vai trò, AC, checklist và gate. 53 User Story là backlog triển khai sản phẩm, không phải 53 chức năng OpenProject đã thực hiện. Estimate/point là mô phỏng; S1–S5 chưa chốt lịch.

`Source ID` là định danh nguồn ổn định; OpenProject ID và Jira key là định danh riêng ở từng tracker. Không dùng chung mapping hoặc suy diễn rằng cùng Source ID cho phép đồng bộ dữ liệu. Core gate staging và nghiệp vụ chưa được cưỡng chế trên live phải được phân biệt theo `openproject/ai/CHECKPOINT.md` và `openproject/README.md`.
