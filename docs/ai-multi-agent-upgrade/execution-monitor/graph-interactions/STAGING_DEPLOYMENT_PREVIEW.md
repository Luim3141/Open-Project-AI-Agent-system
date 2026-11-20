# KẾ HOẠCH VÀ BẢN XEM TRƯỚC TRIỂN KHAI STAGING (DEPLOYMENT PREVIEW)
## TÀI LIỆU KỸ THUẬT: HARDENED STAGING DEPLOYMENT PLAN & READINESS GATES
**Mã tài liệu:** `EM-GI-11`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Principal DevOps Engineer, Release Lead  
**Phiên bản:** 3.0 (Hardened Candidate Release)  

---

### 1. Hiện trạng Môi trường Phục vụ Trực tiếp (Current Staging Baseline)

- **Môi trường:** Staging phục vụ thực tế (Serving Staging via Cloudflare Quick Tunnel)
- **Container Web hiện hành:** `qldapm-ai-stage-staging-web-1`
  - Image ID: `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b`
  - Trạng thái: `Up 5 hours (healthy)` — **NGHIÊM NGẶT BẢO TỒN, KHÔNG THAY ĐỔI**
- **Container Gateway hiện hành:** `qldapm-ai-stage-staging-gateway-1`
  - Image ID: `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`
  - Trạng thái: `Up 5 hours (healthy)` — **BẮT BUỘC GIỮ NGUYÊN 100%**
- **Container Hỗ trợ (Database, Backup, Quick Tunnel, n8n):**
  - Tất cả đang chạy ổn định, không có lỗi khởi động lại (`RestartCount: 0`).
  - Đường hầm Quick Tunnel nội bộ đang phục vụ an toàn.

---

### 2. Thông số Hiện vật Triển khai Dự kiến (Target Hardened Candidate)

- **Candidate Core Image:**
  `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2`
- **Candidate Tag:**
  `qldapm-graph-candidate:final`
- **Overlay Manifest Hash:**
  `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a`
- **Kết quả Kiểm thử Tiền triển khai (Pre-deployment Qualification):**
  - **16/16 Unit Tests** thuật toán hình học và lưu trữ PASS (Node.js).
  - **19/19 Playwright Browser Tests** PASS trên isolated clone.
  - **0** Gemini API calls phát sinh.
  - **0** Database mutations.

---

### 3. Phương thức Triển khai Đề xuất (Deployment Method: Core-Only Rolling Swap)

Tuân thủ nghiêm ngặt quy trình của dự án, việc triển khai sẽ được thực hiện **CHỈ KHI CÓ PHÊ DUYỆT BẰNG VĂN BẢN TỪ CHỦ DỰ ÁN QLDAPM**:
1. **Lệnh thực thi chính thức:**
   ```powershell
   python openproject/ai/provision_local_stage.py --core-only --core-image sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2
   ```
2. **Cơ chế hoạt động:**
   - Script chỉ thay thế container `qldapm-ai-stage-staging-web-1` bằng candidate image đã kiểm định.
   - Gateway, Database, Caddy, Quick Tunnel và n8n không bị khởi động lại.
   - Không chạy lại seeders, không chạy database migrations.
   - Thời gian chuyển đổi (Zero-downtime transition): khoảng 15 đến 25 giây để Rails server khởi động và vượt qua health check `/health_checks/default`.
3. **Bảo toàn Phiên và Khóa TOTP:**
   - Phiên đăng nhập `_open_project_session` và thiết bị TOTP của Actor 7 (PM) được giữ nguyên vẹn trong PostgreSQL, người dùng không bị ép đăng xuất.

---

### 4. Tiêu chí Nghiệm thu Sau Triển khai (Post-Deployment Acceptance Gates)

Ngay sau khi nhận phê duyệt và triển khai:
1. `docker inspect qldapm-ai-stage-staging-web-1` phải khớp chính xác `sha256:79a90c208372...`.
2. Gateway container `qldapm-ai-stage-staging-gateway-1` phải giữ nguyên `sha256:456c38f6a9a9...`.
3. Endpoint `/health_checks/default` trả về HTTP 200 OK.
4. Truy cập giao diện Staging qua Quick Tunnel, kiểm tra tương tác kéo thả node, tự động sắp xếp thông minh và tính năng lưu vị trí cá nhân hóa.

---

### 5. Trạng thái Hiện tại (Current Status)
**READY_FOR_OWNER_APPROVAL**  
*Chưa thực hiện triển khai lên Staging ở phiên này. Toàn bộ hiện vật và kết quả kiểm định đã sẵn sàng chờ lệnh từ Chủ dự án.*
