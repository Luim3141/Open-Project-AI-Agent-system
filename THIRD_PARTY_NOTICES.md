# Giấy phép và thành phần bên thứ ba

OpenProject upstream được pin trong `openproject/upstream-lock.json`. OpenProject có bản quyền của các tác giả upstream và GPL-3.0; bản sao nguyên văn LICENSE/COPYRIGHT được giữ trong `licenses/openproject/`. Source overlay và patch có chứa tác phẩm phái sinh phải tuân thủ điều kiện upstream áp dụng. Không xóa copyright header trong source.

Agent Studio dùng React, React DOM, React Flow, Dagre và esbuild theo lockfile. Giữ `studio.js.LEGAL.txt` cạnh bundle. Python dependencies, n8n, Docker images và các công cụ Jira/Forge có giấy phép riêng; xem metadata/license của phiên bản tương ứng.

Chưa có quyết định của chủ sở hữu về giấy phép chung cho phần code gốc độc lập của dự án. Không tự gán MIT/Apache hay coi repository public là cấp mọi quyền sử dụng. Người tái phân phối phải xác định quyền và nghĩa vụ của từng thành phần; file này không thay thế license upstream.
