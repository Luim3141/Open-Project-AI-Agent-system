# PHƯƠNG ÁN PHỤC HỒI VÀ QUY TRÌNH ROLLBACK KHẨN CẤP
## TÀI LIỆU KỸ THUẬT: HARDENED ROLLBACK & LINEAGE VERIFICATION PROCEDURE
**Mã tài liệu:** `EM-GI-12`  
**Dự án:** QLDAPM — Multi-Agent AI Project Operations Assistant  
**Tác giả:** Principal DevOps Engineer, Release Lead  
**Phiên bản:** 3.0 (Hardened Release Gate)  

---

### 1. Phân tích Bản chất và Rủi ro Kỹ thuật

- **Phạm vi thay đổi của Candidate:** Duy nhất 3 tệp Rails View Templates (`execution.html.erb`, `_execution_style.html.erb`, `_execution_client.html.erb`).
- **Cơ sở dữ liệu:** Không có bất kỳ thay đổi nào đối với cấu trúc bảng (schema), không có migration, không có seeders.
- **Gateway & Gemini Multi-Agent:** Giữ nguyên 100% hình ảnh `sha256:456c38f6a9a936048892bdb2d97fd855eb63c6321fbaceab88de6f8aa56fe70b`.
- **Rủi ro mất mát dữ liệu nghiệp vụ:** **0.0%**. Việc quay lui (rollback) chỉ đơn thuần là việc hoàn nguyên container Web về Image ID tiền nhiệm đã nghiệm thu.

---

### 2. Thông số Hiện vật và Ma trận Lineage Guard

| Thành phần | Hình ảnh Candidate (Khi sự cố) | Hình ảnh Rollback Phục hồi (Baseline đã duyệt) |
|------------|--------------------------------|----------------------------------------------|
| **Core Web ID** | `sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2` | `sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b` |
| **Short ID** | `79a90c208372` | `01274930d1e1` |
| **Tag** | `qldapm-graph-candidate:final` | `qldapm-ui-candidate:final` |
| **Overlay SHA256** | `ef0a5cb3ccc32528119e3a689a8e0175611ff6d614691f9ab2428777af7f075a` | `ebc58f00b886cc600ba31eca5c8044bc48c880314c31f578f0fdac7af3204920` |
| **RootFS Layer Count** | 29 Layers | 28 Layers |
| **Nhãn Bắt buộc** | `org.qldapm.report = actor-daily-read-only` | `org.qldapm.report = actor-daily-read-only` |
| **Gateway Image** | `sha256:456c38f6a9a9...` (Giữ nguyên 100%) | `sha256:456c38f6a9a9...` (Giữ nguyên 100%) |

---

### 3. Chứng Minh Toán Học & Thực Nghiệm Cơ Chế Lineage Guard

Theo hàm kiểm tra tính toàn vẹn `daily_report_core(candidate, previous)` trong `openproject/ai/provision_local_stage.py`:
```python
def daily_report_core(candidate, previous):
    layers = previous['RootFS']['Layers']
    cand_layers = candidate['RootFS']['Layers']
    forward_match = (len(cand_layers) >= len(layers) and cand_layers[:len(layers)] == layers)
    rollback_match = (len(cand_layers) <= len(layers) and layers[:len(cand_layers)] == cand_layers)
    if (not re.fullmatch(r'sha256:[a-f0-9]{64}', candidate['Id'])
            or (candidate['Config'].get('Labels') or {}).get('org.qldapm.report') != 'actor-daily-read-only'
            or not (forward_match or rollback_match)):
        raise ValueError('DAILY_REPORT_CORE_BASE_OR_SCOPE_MISMATCH')
    return candidate['Id']
```

#### A. Triển khai Tiến (Forward Provisioning: Baseline -> Candidate)
- `len(cand_layers) = 29 >= len(layers) = 28`
- `cand_layers[:28] == layers` -> **`forward_match = True`**
- Kết quả: **PASS**

#### B. Quay lui Hoàn nguyên (Rollback Provisioning: Candidate -> Baseline)
- `len(cand_layers) = 28 <= len(layers) = 29`
- `layers[:28] == cand_layers` -> **`rollback_match = True`**
- Nhãn `org.qldapm.report` của baseline là `actor-daily-read-only` -> Thỏa mãn 100%.
- Kết quả kiểm chứng thực tế:
  ```text
  FORWARD MATCH PASS: sha256:79a90c2083727e3355bb7957a0c704bcc51973f3711d3599970690eafac1eff2
  ROLLBACK MATCH PASS: sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b
  ```
  -> **Khẳng định ChatGPT cảnh báo không áp dụng cho bản thiết kế này: `provision_local_stage.py` KHÔNG BAO GIỜ từ chối rollback về baseline `01274930d1e1`.**

---

### 4. Quy trình Thực thi Quay lui Chính Thức (Standard Provisioning Rollback)

Loại bỏ hoàn toàn cách làm tạm bợ `docker run` thủ công. Quy trình chính thức được bảo vệ bởi Docker Compose và provisioning tooling:

#### Bước 1: Kích hoạt Rollback qua công cụ Provision chính thức
```powershell
python openproject/ai/provision_local_stage.py --core-only --core-image sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b
```

#### Cơ chế vận hành tự động của script:
1. Xác thực Lineage Guard (`rollback_match = True`).
2. Khóa image lock tại `$env:LOCALAPPDATA\QLDAPM\openproject-ai\stage-image-lock.json` trỏ về `01274930d1e1`.
3. Kích hoạt Docker Compose tái tạo `staging-web` (`docker compose up -d --no-deps --no-build --pull never staging-web`).
4. Bảo toàn 100% volumes, bind mounts, networks, security options, healthchecks và Compose metadata.
5. Kiểm tra tự động endpoint `/health_checks/default` cho đến khi đạt HTTP 200 OK.

---

### 5. Phương Án Dự Phòng: Compose-Native Rollback (Không dùng `docker run`)

Trong tình huống khẩn cấp nếu script Python bị khóa do tiến trình khác:
```powershell
# 1. Cập nhật image pin trong lockfile về baseline 01274930d1e1
$lockPath = "$env:LOCALAPPDATA\QLDAPM\openproject-ai\stage-image-lock.json"
$lock = Get-Content $lockPath | ConvertFrom-Json
$lock.'staging-web' = "01274930d1e1"
$lock | ConvertTo-Json | Set-Content $lockPath

# 2. Yêu cầu Docker Compose tải lại container staging-web với cấu hình nguyên bản
docker compose -p qldapm-ai-stage -f "$env:LOCALAPPDATA\QLDAPM\openproject-ai\stage\docker-compose.yml" up -d --no-deps --no-build --pull never staging-web
```
- **Ưu điểm vượt trội:** Giữ trọn vẹn nhãn quản lý Compose (`com.docker.compose.project`, `com.docker.compose.service`), mạng lưới nội bộ, volumes gắn kết và không bao giờ tạo container "mồ côi" (orphan).

---

### 6. Quy trình Kiểm tra Xác nhận sau Quay lui (Post-Rollback Verification)

1. **Xác minh Container Runtime:**
   ```powershell
   docker inspect qldapm-ai-stage-staging-web-1 --format '{{.Image}}'
   # Kết quả mong đợi: sha256:01274930d1e1f2a7e9ad8bfdaf33ef07dbf11d9234bbe39fb61417b3ed45325b
   ```
2. **Kiểm tra Phản hồi HTTP:**
   ```powershell
   curl.exe -s -I http://127.0.0.1:18091/health_checks/default
   # Kết quả mong đợi: HTTP/1.1 200 OK
   ```
3. **Kiểm tra Quick Tunnel:** Truy cập Staging xác nhận giao diện Execution Monitor phục hồi về trạng thái Candidate UI/UX đã được phê duyệt.
4. **Kiểm tra Không có Drift:** Đối chiếu `git status` đảm bảo working tree sạch.
