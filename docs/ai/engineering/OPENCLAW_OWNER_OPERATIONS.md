# CẨM NANG VẬN HÀNH OPENCLAW GATEWAY CHO PROJECT OWNER
## Khắc Phục Khóa Tiến Trình Windows (setup.lock), Quản Trị WSL2 Runtime & Kết Nối Cổng 18789

**Dự án:** QLDAPM MAIN — Project 6 (`ai-dev-demo`)  
**Mục tiêu:** Hướng dẫn Project Owner làm chủ hoàn toàn OpenClaw Runtime trên Windows 11 & WSL2, xử lý triệt để lỗi `setup.lock`, và quản trị các tác nhân AI OpenClaw (Dev, Reviewer, QA).

---

## 1. Bản chất sự cố Khóa Tiến trình (`setup.lock`) trên Windows

### 1.1. Hiện trạng ghi nhận thực tế
- File khóa: `C:\Users\LUIM\AppData\Roaming\OpenClawTray\setup.lock` (dung lượng 57 bytes).
- Thông điệp lỗi khi chạy Setup UI:  
  `The process cannot access the file because it is being used by another process.`
- Tiến trình đang chiếm dụng file lock: **PID 22996** (`OpenClaw.Tray.WinUI.exe`), đã chạy nền liên tục từ ngày 29/10/2026.

### 1.2. Nguyên nhân cốt lõi (Root Cause)
Theo phân tích từ nhật ký cài đặt `setup-engine-20261029-141300.journal.jsonl`:
1. Vào ngày 29/10/2026, trình cài đặt OpenClaw Tray WinUI cố gắng cài đặt OpenClaw trên môi trường Windows Host bằng Node.js v24.19.0.
2. Quá trình thiết lập bị lỗi do xung đột môi trường Windows native, hệ thống đã kích hoạt cơ chế hoàn tác (Rollback).
3. Tuy nhiên, tiến trình giao diện khay hệ thống `OpenClaw.Tray.WinUI.exe` không tự động thoát, dẫn đến handle của file `setup.lock` tiếp tục bị giữ độc quyền trong kernel Windows.
4. Mọi lần chạy trình cài đặt sau đó đều bị Windows chặn với lỗi truy cập file.

---

## 2. Thực trạng Kiến trúc: OpenClaw Đã Đang Chạy Hoàn Hảo Trong WSL2!

> [!IMPORTANT]
> **Project Owner KHÔNG CẦN và KHÔNG NÊN cài đặt lại OpenClaw trên Windows Host.**  
> Kiến trúc chuẩn của QLDAPM MAIN đã triển khai toàn bộ OpenClaw Gateway và AI Workers bên trong máy ảo nhẹ **WSL2 Distro `OpenClawGateway`**.

Bằng chứng đối soát trực tiếp từ hệ thống:
- **Distro WSL2:** `OpenClawGateway` (chạy Ubuntu/Linux, cách ly và bảo vệ an toàn cho Windows host).
- **Node.js runtime:** Node.js v24.22.2 (phiên bản ổn định chuẩn doanh nghiệp).
- **Cổng dịch vụ Gateway:** Cổng `18789` lắng nghe trên `0.0.0.0:18789` (truy cập thông suốt từ cả WSL2 và Windows host tại `http://127.0.0.1:18789`).
- **Tiến trình Gateway đang chạy:** PID **30953** bên trong WSL2 (`node /home/openclaw/openclaw/dist/index.js gateway --port 18789`).
- **Test Server Mini Task Manager:** PID **31498** đang chạy phục vụ kiểm thử end-to-end trên `/home/openclaw/engineering/mini-task-manager-server.py`.

---

## 3. Các lệnh PowerShell dành cho Owner để xử lý `setup.lock`

Mở **PowerShell (Run as Administrator hoặc User bình thường)** và thực hiện theo nhu cầu:

### Bước 1: Kiểm tra tiến trình đang giữ file lock
```powershell
Get-Process -Name "OpenClaw.Tray.WinUI" -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime, Responding
```

### Bước 2: Dừng tiến trình Tray UI bị treo để giải phóng lock
```powershell
Stop-Process -Name "OpenClaw.Tray.WinUI" -Force -ErrorAction SilentlyContinue
Write-Host "Da dung tien trinh OpenClaw.Tray.WinUI thanh cong." -ForegroundColor Green
```

### Bước 3: Xóa file `setup.lock` dư thừa
```powershell
$lockPath = "$env:APPDATA\OpenClawTray\setup.lock"
if (Test-Path $lockPath) {
    Remove-Item -Path $lockPath -Force
    Write-Host "Da xoa file lock: $lockPath" -ForegroundColor Green
} else {
    Write-Host "File lock khong con ton tai." -ForegroundColor Yellow
}
```

---

## 4. Quản trị & Giám sát OpenClaw Gateway trong WSL2 từ Windows

Project Owner có thể kiểm tra và điều khiển OpenClaw Gateway hoàn toàn thông qua PowerShell bằng các lệnh chuẩn sau:

### 4.1. Kiểm tra trạng thái kết nối mạng tới Gateway
```powershell
# Kiem tra ket noi HTTP tu Windows Host toi cong 18789
curl.exe -s -I http://127.0.0.1:18789
```
*Kết quả kỳ vọng:* Trả về `HTTP/1.1 200 OK` hoặc phản hồi JSON từ OpenClaw Gateway.

### 4.2. Xem tiến trình OpenClaw bên trong WSL2
```powershell
wsl -d OpenClawGateway ps aux | grep openclaw
```
*Kết quả quan sát được:* Tiến trình Node.js chạy `dist/index.js gateway --port 18789`.

### 4.3. Khởi động lại Gateway trong trường hợp cần bảo trì
Nếu muốn khởi động lại dịch vụ Gateway trong WSL2:
```powershell
# Dung tien trinh cu
wsl -d OpenClawGateway pkill -f "openclaw"

# Khoi dong lai Gateway o che do daemon nen
wsl -d OpenClawGateway nohup node /home/openclaw/openclaw/dist/index.js gateway --port 18789 > /home/openclaw/gateway.log 2>&1 &
```

### 4.4. Đọc nhật ký thời gian thực (Live Logs) của OpenClaw
```powershell
wsl -d OpenClawGateway tail -n 50 -f /home/openclaw/gateway.log
```

---

## 5. Kết nối Giao diện OpenClaw Tray WinUI với Gateway đang chạy

Nếu Owner muốn sử dụng giao diện khay Desktop (`OpenClaw.Tray.WinUI`):
1. Đảm bảo đã thực hiện **Mục 3** để xóa `setup.lock`.
2. Chạy lại `OpenClaw Tray` từ Start Menu.
3. Trong phần cấu hình kết nối, chọn:
   - **Mode:** `Remote / Existing Gateway`
   - **Host:** `127.0.0.1`
   - **Port:** `18789`
   - **Token:** Đọc từ file cấu hình `/home/openclaw/.openclaw/config.json` nếu có bật xác thực.
4. Giao diện sẽ hiển thị trạng thái `Connected (WSL2 Gateway Online)` màu xanh mà không cần chạy lại bộ cài đặt.

---

## 6. Phân định vai trò tác nhân: Ai làm gì?

| Tác nhân | Nơi thực thi | Mô hình / Công nghệ | Trách nhiệm |
| :--- | :--- | :--- | :--- |
| **Supervisor** | QLDAPM Gateway Container | Python Deterministic Pipeline | Tiếp nhận lệnh, claim atomic, điều phối DAG, ghi nhận receipt |
| **PM & BA** | QLDAPM Gateway Container | Gemini API (`gemini-3.5-flash-lite`) | Phân tích yêu cầu, bóc tách WBS, sinh tiêu chí nghiệm thu |
| **Dev Agent** | WSL2 `OpenClawGateway` | OpenClaw Runner + Tool Sandbox | Sinh mã nguồn, chỉnh sửa file, quản lý branch, tạo commit |
| **Reviewer Agent** | WSL2 `OpenClawGateway` | Exact-Diff Static Analyzer | Đối chiếu mã nguồn thực tế với PR spec, chống hallucination |
| **QA Agent** | WSL2 `OpenClawGateway` | Pytest Execution Sandbox | Chạy kiểm thử tự động, trích xuất output và bắt log lỗi |

Toàn bộ chu trình hoạt động khép kín, an toàn và có đầy đủ bằng chứng lưu tại SQLite `/state/gateway.sqlite`.
