# Kiểm tra bản xuất bản

Ngày kiểm tra: 20/11/2026 (Asia/Bangkok). Chạy trên bản source đã lọc tại checkout xuất bản, dùng dependencies đã có trên máy, không gọi provider hay sửa live runtime.

| Kiểm tra | Kết quả local |
| --- | --- |
| Publication tool tests | 3 PASS; bao gồm đọc đúng staged bytes dù working tree khác, không in secret và từ chối ghi đè checkout |
| Historical credential digest guard | 2 PASS |
| Agent Observer | 19 PASS |
| Agent models | 5 PASS |
| Prompt injection / secret exfiltration | 5 PASS |
| Backup/restore drill, synthetic offline | 3 PASS |
| Agent Studio frontend tests | 16 PASS |
| Agent Studio frontend build | PASS, esbuild và bundle có legal notices |
| Python source syntax | 1.397 file parse thành công trước bổ sung fixture cuối; fixture cuối được chạy lại trong suite tương ứng |
| Development patch | `git apply --check` và apply PASS; 35 tracked paths và 5 untracked paths khớp source development gốc sau chuẩn hóa CRLF/LF |
| Whitespace ở file publication mới/sửa | PASS |

Publication checker quét toàn bộ Git index trước commit, không báo vi phạm theo các pattern API keys/private keys/runtime paths đã định nghĩa. Ngoài checker còn có rà soát exact-match các giá trị nhạy cảm lấy từ cấu hình private có giới hạn, credential digest lịch sử và lọc credential fields trong JSON. Không lưu credential thô trong báo cáo public.

Giới hạn: không chạy toàn bộ regression/live E2E, không cài lại từ đầu trên Windows mới, không chạy Docker setup/rollout, không chứng nhận RAG/performance/production. Giữ nguyên whitespace có sẵn trong source và báo cáo lịch sử, thay vì format lại hàng nghìn file. Các báo cáo lịch sử đã lọc credential có thể không còn khớp byte/hash gốc; không dùng chúng như artifact nguyên bản để xác minh lại deployment cũ.

CI trên GitHub chạy lại các suite offline và frontend từ dependencies/lockfile. Kết quả GitHub Actions là nguồn xác minh riêng cho môi trường Linux, không được suy ra từ local PASS.
