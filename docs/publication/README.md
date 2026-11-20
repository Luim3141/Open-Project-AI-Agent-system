# Phạm vi xuất bản — 20/11/2026

Đây là snapshot source đã vệ sinh, có main history mới. Lịch sử Git gốc, mọi file gốc và backup bundle được giữ tại workspace gốc; không push các branch/history chưa quét.

Bao gồm source ứng dụng, overlay, frontend, tests, deployment configs, lockfiles, workflow, Markdown/JSON evidence và patch development riêng. `source-manifest.json` ghi hash/size của bản public sau khi lọc và bổ sung tài liệu, loại trừ chính manifest, Git metadata và dependencies local. Git commit là nguồn xác định snapshot cuối cùng.

Giữ local: credentials/runtime, database, backup, virtualenv/node_modules, model cache, packaged candidate trùng source, log, ảnh/chụp màn hình và Word/PDF chưa được kiểm nội dung riêng. Tài liệu đánh giá cá nhân và hội thoại private không đưa vào GitHub. Vì vậy các link lịch sử tới bằng chứng bị giữ local có thể không mở được.

Credential thật đã nhận diện được thay bằng marker `PUBLICATION_REDACTED`. Live scripts tương ứng cần cấp lại cấu hình riêng trước khi sử dụng; không xem marker là dữ liệu có thể chạy. Tests redaction guard dùng digest thay vì lưu credential lịch sử.

Không thay đổi Docker services, database, Jira, Telegram, provider hoặc hệ thống live để xuất bản. Không suy ra feature hoàn tất, giấy phép chung, production readiness hay bằng chứng mới từ việc upload.

Xem `export-summary.json` cho thống kê lần export; kết quả kiểm tra và giới hạn trong `VALIDATION.md`.
