# Giao diện và tương tác

**COMPLETE_ON_STAGING — 2026-10-19T19:59:52.412347+07:00**. [Serving deployment report](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md);30publicUI/API checksPASS. Qualification evidence below records pre-deployment validation.

Native OpenProject shell, typography và blue palette; card overview8metrics; metadata run/trace/actor-role/project/time/model. Dashboard trạng thái bằng chữ và màu, completed checkmark, failed marker.

SVG graph dùng topological levels, layout bands2columns để đọc trên màn hình trình chiếu. Assignment dashed, dependencies solid; hover/title, node keyboard Enter/Space; selected ancestor dependencies highlight. Zoom ±, fit, background pan, compact/expanded nodes. Table fallback luôn có; mobile≤760px tự mở bảng.375px không tràn ngang window.

Detail: mục tiêu, được giao bởi, dependencies, input source IDs, start/end/duration, actual model usage, retry/error codes, validation/output/limitations. Supervisor phân biệt GEMINI_MODEL_PLAN với LOCAL_REGISTERED_ROUTING. Thiếu dữ liệu hiển thị rõ; legacy output có origin riêng.

Timeline lọc agent, timestamp Asia/Bangkok, không raw JSON. Replay1event/giây là tốc độ trình chiếu do UI chọn, không giả lập tốc độ lịch sử; playback/slider/present tái xác thực qua endpoint đọc. Intermediate replay ẩn final agent output; về cuối xem output lưu.

Polling1run/3s khi active, timeout25s, backoff2..30s tối đa6failures, pause tab hidden/pagehide, stop terminal. Network/auth failure xóa nội dung nhạy cảm cũ; reconnect chỉ GET. Chọn node terminal/replay reauthorize Native nguồn trước khi đọc.

History10rows/page; search≤160, state filter, asc/desc, empty/error states. Không thêm menu trùng lặp. Dark monitor panel theo prefers-color-scheme, không thay theme toàn OpenProject. Focus outline, min44px controls, reduced-motion.


Post-deployment acceptance: [STAGING_DEPLOYMENT_REPORT](run_20261019_1635/deployment/STAGING_DEPLOYMENT_REPORT.md). Exact servingpair456c38f6/7d76c1eb;30publicchecksPASS, ledger517unchanged. Ownerapproval61e1719f preserved; previewfile remains the immutable approved plan, not current deploymentstate.
