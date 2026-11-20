# Browser tool diagnostic — 12/10/2026

## Kết quả

Người dùng yêu cầu chẩn đoán/khôi phục Computer Use từng lưu A03. Đã kiểm tra local và đăng ký lại plugin chính thức; browser tool **chưa được khôi phục trong phiên hiện tại**. Không Jira writes, không restart app hoặc reload draft A04.

## Bằng chứng

- Trước gián đoạn: `mcp__cua_repl.js` đã lưu A03 UUID `01a12ee4-1276-76b4-ba01-49bdeda52f9d`; đây là browser runtime, khác native Windows `@oai/sky`.
- Hiện tại: tìm `cua` trong `ALL_TOOLS` trả `[]`, `tools.mcp__cua_repl__js` là `undefined`; `list_mcp_resources(server="cua_repl")` trả resources rỗng. Resources rỗng một mình không chứng minh server hỏng; tool không exposed là phép kiểm tra quyết định cho thao tác browser.
- `codex plugin list --marketplace openai-bundled --available --json`: browser/chrome/computer-use/unified-computer-use đều installed=true, enabled=true; unified version26.1007.21434.
- `.mcp.json` của unified: entry và Node executable tồn tại, enabled surfaces=browser; backends=chrome,iab,mcpapps. Process Node tương ứng tồn tại; process/PID không phải bằng chứng tool có thể gọi.
- App package `OpenAI.Codex` version26.1007.2314.0, Status Ok.
- Log `codex-desktop-ffd5915e-7952-46fa-a794-d33d43cec6c8-14564-t0-i1-123438-0.log`: dòng177 tại12:36:17Z ghi plugin_uninstall_succeeded unified-computer-use; dòng264/265/317/677 ghi browser_use_availability_resolved available=false reason=statsig-disabled; nhiều dòng ghi mcp_extension_server_tools_empty server=cua_repl. Đây là trạng thái được ghi lúc19:36–20:12 +07, không bằng chứng người dùng thiếu quyền Jira hoặc xác định ai đã gỡ plugin.

## Khôi phục đã thử

Đọc CLI help trước; chạy `codex plugin add unified-computer-use@openai-bundled --json` thành công exit0, cài/đăng ký đúng gói bundled hiện có, không gỡ gói hoặc nâng bản. Đọc lại installed/enabled đều true. Sau thao tác, `ALL_TOOLS` vẫn không có cua; chưa có browser call để chứng minh phục hồi.

Không chỉnh Statsig/feature gate, không force permissions, không tự tạo MCP client/helper protocol, không đọc cookie/token/browser storage, không thay credential hoặc bật billing. Không kill app/helper: draft browser A04 chưa lưu và các cửa sổ người dùng phải được giữ.

## Diễn giải và giới hạn

Kiểm tra phục hồi tiếp theo: log app có phiên mới khởi động20:40 +07; plugin vẫn installed/enabled. Đã gọi `mcp__node_repl__js_reset`, import lại `@oai/sky` và `list_windows` thành công (`runtimeReady=true`,6window). Native Windows runtime hoạt động; danh sách `cua` vẫn rỗng. Vì vậy reset Node không phục hồi app-managed browser tool và không được gọi là sửa xong. Không mở/sửa UI app ChatGPT, không ép feature gate, không Jira writes.

Các kiểm tra loại trừ thiếu file runtime hoặc đơn giản plugin disabled trong config. Bằng chứng chỉ tới tầng app-managed availability/tool registration; chưa xác định được nguyên nhân sâu hơn khiến gate bị disable. Reinstall local chưa sửa được tool registry của phiên. Không cam kết restart app/chat sẽ khắc phục; chưa thử vì cần bảo toàn draft đang mở.

Hướng khắc phục được OpenAI công bố gồm xác minh kết nối browser, thử phiên mới, restart/update app, và /feedback nếu vẫn lỗi: https://learn.chatgpt.com/docs/chrome-extension#troubleshooting . Hướng dẫn này chủ yếu cho browser extension; không tự chứng minh lỗi IAB hiện tại có cùng nguyên nhân.

A04 vẫn draft chưa lưu; A05 chưa tạo; monitor PAUSED. Không được đánh dấu các rule/E2E hoàn tất từ kết quả diagnostic này.
