# Implementation proof — Agent Studio V2

## V1 thực tế

Baseline source commit `52fa710`: view `core/overlay/app/views/qldapm_ai/observer.html.erb` render `_observer_client`; client tạo DOM cards từ `snapshot.stages`. Route V1 không import/mount React Flow, không có edge renderer, Dagre layout hoặc graph viewport. Việc đổi màu card không giải quyết pan/zoom/dependency/inspector. Navigation cũ còn bắt mọi `.qcc-nav-item` và `preventDefault()` trước khi kiểm `data-tab`, nên chặn anchor Studio; actual Main UAT đã bắt lỗi này.

## Source V2

Tất cả đường dẫn dưới tính từ `openproject/ai/`:

| File | Bằng chứng implementation |
|---|---|
| `core/agent-studio-v2/studio.jsx` | Import thật React/ReactDOM/`@xyflow/react`; `createRoot` mount `Studio`; custom `AgentNode`, `EvidenceEdge`, `Inspector`, `Events`, `ArtifactList`, typed `Output`; production `<ReactFlow>` với Controls/MiniMap/Background, keyboard/click/hover và markers |
| `core/agent-studio-v2/model.mjs` | `validateSnapshot`/`validateMonitor`; `graph` tạo nodes từ canonical stages, edges từ actual monitor `from/to/kind`; không tạo dependency từ thứ tự card. Dagre rankdir LR/TB; actual attempts từ monitor, quan hệ ATTEMPT_ORDER không giả handoff |
| `core/agent-studio-v2/studio.css` | Tokens dark/light; animated dash/pulse chỉ qua active classes; reduced motion; container queries; native select override trong scope |
| `core/agent-studio-v2/build.mjs` | esbuild IIFE production, local CSS bọc `@scope (#qldapm-agent-studio)`, SHA256 manifest, metafile evidence; không CDN |
| `core/agent-studio-v2/package-lock.json` | Pinned resolved/integrity packages, React Flow/Dagre/React/esbuild |
| `core/agent-studio-v2/build-proof.json` | Inputs thật từ `node_modules/@xyflow/react` và Dagre, outputs và asset hashes |
| `core/overlay/public/qldapm-agent-studio-v2/` | Production JS/CSS, manifest và bundled license notices được COPY vào immutable Core |
| `core/overlay/app/views/qldapm_ai/observer.html.erb` | Rails authenticated mount root, project-scoped endpoints, assets từ local public path kèm content hash và CSP nonce; không render client V1 |
| `core/overlay/app/controllers/qldapm_ai_controller.rb` | Giữ signed bridge/Native ACL; observer list limit20 mặc định và validation1..50; Task/run route hiện hành giữ nguyên |
| `core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb` | Entry point `qcc-agent-studio-link`; tab delegation chỉ bắt `.qcc-nav-item[data-tab]`, anchor đi đúng route |

Không thêm một node cho mỗi model call. Không thêm BA/PM parent379 vào Task397. Edge animation có nghĩa destination stage active/fresh, không khẳng định truyền message/handoff liên tục. Không có handoff event thì tooltip ghi chưa ghi nhận timestamp, chỉ dẫn contract evidence.

## Transport và lifecycle

Không tìm thấy Observer/Gateway SSE/EventSource route trong source đang chạy. Rails bridge đang request/response đồng bộ; giữ connection để loop polling phía server sẽ chiếm Puma thread, không phải tái sử dụng một stream thật. V2 dùng bounded adaptive polling:3s khi canonical RUNNING/FRESH,15s terminal, backoff tối đa60s; không overlap, timeout90s, tabẩn dừng, đổi Task hủy request và generation guard. Freshness dựa source timestamp/TTL120s, tách khỏi lần GET thành công.

React root không có key theo revision; status updates giữ viewport/selection. Task đổi và thay hướng layout mới fit; render historical attempts không che mất run trước. MutationObserver và Turbo lifecycle unmount, hủy timer/requests; một bộ global handlers trên mỗi document. ResizeObserver của island được disconnect khi unmount. Hover dùng dữ liệu đã tải, không gọi model.

## Primary sources đã đọc

[xyflow source repository](https://github.com/xyflow/xyflow), [React Flow layouting](https://reactflow.dev/learn/layouting/layouting), [ReactFlow API](https://reactflow.dev/api-reference/react-flow). Dùng custom nodes/edges và Dagre như integration trên; không sử dụng paid Pro service.
