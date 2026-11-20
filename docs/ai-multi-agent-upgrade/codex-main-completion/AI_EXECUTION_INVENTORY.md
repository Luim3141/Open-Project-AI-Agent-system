# Execution inventory — Main và Staging

Inventory ban đầu20/10 (`execution-inventory.json`) xác nhận Main0ai_runs/0agent_runs/0providerreceipts; Stage113ai_runs/23agent_runs/44providerreceipts. Vì lưu trữ độc lập, Main0history là dữ liệu thực, không phải bằng chứng tự thân của lỗi UI. Actor isolation còn lọc đúng người gọi.

Sau UAT, Main có một local run thật `87803ca8-72a1-4643-b00f-8fda05a06266`, actor19/project5,COMPLETED, PM/Reviewer,14executionevents và kết quả hiển thị trên UI. Main provider smoke chỉ cập nhật usage/readiness, không tạo agent run hoặc gắn receipt giả vào run local. Runtime08:31: Main1ai_run/1agent_run/14events/0proposals/0providerreceipts; local Gemini ledger2. Stage counts113/23/44,usage517 giữ nguyên.

Manifest23Stage agent runs có13ownership conflicts;11runs có generation receipts. Các trạng thái receipt như HTTP_SUCCESS/LIVE_SUCCESS/INVALID_RESPONSE phải giữ nguyên; không chuyển tất cả thành SUCCEEDED. Tất cả nội dung vẫn UNREVIEWED, chưa export sensitive payload sang Main.

Dữ liệu định lượng là inventory tại thời điểm ghi, không phải số lượng executions mà mọi role đều được phép đọc. Nguồn: `AI_EXECUTION_MIGRATION_MANIFEST.json`, `runtime-20261021-083112.json`, `main-execution-history-filtered.txt`, `main-native-views-security-readback.json`.
