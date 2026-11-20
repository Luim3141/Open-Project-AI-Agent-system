# BÁO CÁO ĐỐI CHIẾU SOURCE — IMAGE — RUNTIME PARITY
## EXECUTION MONITOR UI/UX REFINEMENT

- **Mục tiêu:** Chứng minh tính đồng nhất tuyệt đối (Parity) giữa mã nguồn trên đĩa, Docker candidate image, và các container đang phục vụ trên Staging.
- **Thời điểm kiểm tra:** 2026-10-20 01:05:54
- **Kết luận:** **PARITY VERIFIED 100% (KHỚP TỪNG BYTE)**

---

### 1. Bảng Đối Chiếu Băm SHA-256 Các File Source View

Chỉ có đúng 4 file Rails view partials được chỉnh sửa trong toàn bộ đợt nâng cấp UI/UX này:

| Đường dẫn file tương đối | Băm SHA-256 trên Đĩa (`openproject/ai/core/overlay/...`) | Băm SHA-256 trong Container (`/app/app/views/qldapm_ai/...`) | Trạng thái đối chiếu |
|--------------------------|----------------------------------------------------------|---------------------------------------------------------------|:--------------------:|
| `app/views/qldapm_ai/_execution_style.html.erb` | `8aaf64822216ec393ff525c7f8922ae53584aaf09c667786d00feab7c806ecdc` | `8aaf64822216ec393ff525c7f8922ae53584aaf09c667786d00feab7c806ecdc` | **MATCH (100%)** |
| `app/views/qldapm_ai/_execution_client.html.erb` | `a9eff3ebefb23044854d4ec18fb85a2bb24ea8dbaa68d2cd81e7822f82c2fa5a` | `a9eff3ebefb23044854d4ec18fb85a2bb24ea8dbaa68d2cd81e7822f82c2fa5a` | **MATCH (100%)** |
| `app/views/qldapm_ai/execution.html.erb` | `27d91ba222b06c69d78c6bec6b038941d12939f5aad20c6e8e5af3218a4a2f6e` | `27d91ba222b06c69d78c6bec6b038941d12939f5aad20c6e8e5af3218a4a2f6e` | **MATCH (100%)** |
| `app/views/qldapm_ai/executions.html.erb` | `20c8556e1514f9f9acf5c4db65b0aa0a174ba612b758b03feff6a095421f4cac` | `20c8556e1514f9f9acf5c4db65b0aa0a174ba612b758b03feff6a095421f4cac` | **MATCH (100%)** |

---

### 2. Tổng Hợp Băm Lớp Phủ (Source Overlay Manifest Hash)

- **Thuật toán tạo băm:** Ghép nối các cặp `(filename, sha256)` theo thứ tự bảng chữ cái và tính SHA-256 tổng thể.
- **Giá trị băm kỳ vọng:** `ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920`
- **Label trong Docker Image:**
  `org.qldapm.source.sha256 = ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920`
- **Label đọc từ container đang chạy:**
  `docker inspect qldapm-ai-stage-staging-web-1` trả về chính xác:
  `org.qldapm.source.sha256 = ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920`
- **Trạng thái:** **MATCH (100% Khớp)**

---

### 3. Cấu Trúc Lớp (RootFS Layers Parity)

Kiểm tra số lượng và mã băm các lớp trong Docker image:

1. **Baseline Core Image (`sha256:7d76c1eb...`):**
   - Tổng số layers: 27 layers.
   - Layer cuối cùng: `sha256:0979d98e8d2cc0ab7fe99be71a789facb9d8e34f291361d54e09a9b65155dd2d`.

2. **Candidate Core Image (`sha256:01274930...`):**
   - Tổng số layers: 28 layers.
   - 27 layers đầu tiên: **HOÀN TOÀN TRÙNG KHỚP 100%** với baseline image.
   - Layer thứ 28 (Lớp duy nhất bổ sung): `sha256:df23f9fd4edb0da259c075cf4fa9cd01a16c91cf6b3d70661c87ef7114e8e815` (chứa đúng 4 file view UI mới).

3. **Tính kế thừa và khả năng khôi phục (Lineage Integrity):**
   - Candidate là con trực tiếp (direct descendant) của baseline.
   - Không chứa bất kỳ thay đổi nào về thư viện bundle, binary, cấu hình OS hay database client.
   - Đáp ứng đầy đủ quy tắc Lineage Guard trong `provision_local_stage.py`.

---

### 4. Khóa Trạng Thái Môi Trường (`stage-image-lock.json`)

Nội dung file khóa trên host tại `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\stage-image-lock.json`:
```json
{
  "staging-web": "sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b",
  "staging-gateway": "sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b",
  "db": "sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3"
}
```

Đối chiếu với các container đang chạy:
- Container `qldapm-ai-stage-staging-web-1`: `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b` -> **KHỚP**
- Container `qldapm-ai-stage-staging-gateway-1`: `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b` -> **KHỚP**
- Container `qldapm-ai-stage-db-1`: `sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3` -> **KHỚP**

---

### 5. Kết Luận
Tính nhất quán ba bên giữa **Source Code (Đĩa)** — **Docker Image (BuildKit)** — **Runtime Container (Puma)** đã được xác minh toàn diện và độc lập. Không có hiện tượng drift code hay sai lệch phiên bản.
