# Main / Staging runtime parity — 21/10/2026

Nguồn read-only: `source-image-runtime-current.json` lúc08:38+07, `runtime-20261021-083112.json`; danh sách Docker08:42 có18serving và2owned qualification clones. Healthchecks healthy khi có; worker/cron đang chạy. Không gọi20containers là20dịch vụ sản phẩm.

| Thành phần | Main | Staging |
|---|---|---|
| Native Core | localhost8088, project5,329WP | localhost18091, project3,335WP |
| Core image | `sha256:95da6c8eed2e9cae1bc023b7f29451433bec3e1c68480421be1c4629542ef53f` | `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` |
| Gateway image | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` | `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` |
| Gateway URL | localhost8090 | localhost18092 |
| Core source/runtime |47/47 match |44/47 match với source hiện hành |
| Active Gateway Python |51match,0modified |51match,0modified |

Ba khác biệt Core Stage/source: `qldapm_ai_controller.rb`, `qldapm_ai/show.html.erb`, `qldapm_work_packages/_navigation.html.erb`. Stage giữ deployment độc lập trước đó; không tuyên bố hai môi trường đã cùng Core image. Bảy historical Gateway Python modules không nằm trong image; số51chỉ tính Python, không so với thống kê53bao gồm định dạng khác.

PostgreSQL volumes, Gateway writable state và actor mappings tách biệt. MainPM19/BA20/BE21/FE22/QA23; Stage actor IDs khác và một số login có role đảo, không copy wholesale config/SQLite/credentials. Cùng Gemini Google project nên quota thực tế chia sẻ dù local ledgers tách biệt; guard429/fail-closed và no-paid-fallback vẫn áp dụng.

QuickTunnel Stage được đọc từ localhost18090 lúc08:31: https://leadership-museum-framed-scanned.trycloudflare.com . Đây là hostname động, phải đọc lại khi khởi động/đứt tunnel. Không public Main. n8n, Second Brain, Tunnel, Stage DB/Gateway/Core và CSDLDPT giữ nguyên serving identity qua đợt deploy Main (15containers ngoài baMainCore giữ nguyên).

Main/Stage chạy đồng thời được xác minh bằng runtime và API; không bao gồm capacity20 hoặc restart toàn Docker để thử phục hồi lần nữa.
