# HỒ SƠ PHÁP Y M3: KIỂM TOÁN MÔI TRƯỜNG RUNTIME OPENCLAW (WSL2)
> Thời điểm kiểm toán: `2026-10-30 20:29:35 UTC`  
> WSL2 Distribution: `OpenClawGateway` (Ubuntu 24.04 LTS)  
> Process PID: 30953 (Node.js v24.22.2)  
> Trạng thái kiểm toán: **HOÀN TOÀN TRUNG THỰC THEO RUNTIME ĐANG CHẠY**

---

## 1. THÔNG SỐ RUNTIME VÀ TIẾN TRÌNH OPENCLAW

1. **Phiên bản nhị phân & Commit:**
   - Phiên bản: `OpenClaw 2026.10.8 (dc2523e)`
   - Đường dẫn thực thi: `/usr/local/bin/openclaw`
   - Node runtime: `/home/openclaw/.openclaw/tools/node-v24.22.2/bin/node`
   - Memory allocation: `--max-old-space-size=5906`
2. **Cổng dịch vụ & Network Binding:**
   - Port: `18789` (TCP LISTEN trên `127.0.0.1` và `::1`)
   - File descriptor: fd=91 (IPv4), fd=92 (IPv6)
   - Loopback mode: `bind: "loopback"` (cấm lắng nghe ra ngoài card mạng vật lý)
   - Xác thực: Bearer Token cố định trong cấu hình `auth.mode: "token"`.
3. **Sức khỏe dịch vụ (Health Check):**
   - HTTP GET `http://127.0.0.1:18789/`: `{"ok":true,"status":"live"}`
   - Event Loop latency: `max=38ms`, `p99=38ms`, `util=0.12`, `cpu=0.141`.
   - Check duration: `69ms`.

---

## 2. KIỂM TOÁN RANH GIỚI BẢO MẬT HỆ ĐIỀU HÀNH (OS SANDBOXING)

- **User Execution:** Tiến trình OpenClaw chạy dưới tài khoản không đặc quyền `openclaw:openclaw` (UID 1000).
- **Quyền Root:** `elevated.enabled: false` (không thể chạy `sudo` hoặc leo thang đặc quyền root).
- **Filesystem Sandbox:** `tools.fs.workspaceOnly: true`. OpenClaw bị giam hoàn toàn trong thư mục workspace được chỉ định.
- **Network Egress Containment:**
  * Bị chặn hoàn toàn các công cụ ra internet: `deny: ["sessions_spawn", "sessions_send", "cron", "gateway", "message", "web_search", "web_fetch"]`.
  * Không thể gửi dữ liệu ra bên ngoài hoặc tải thêm mã độc từ internet.
