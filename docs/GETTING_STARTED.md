# Cài đặt clone mới

## 1. Source và quyền

Clone repository, đọc README và security policy. Dùng môi trường riêng, không trỏ clone mới vào production runtime. Các đường dẫn `D:\AI project\QLDAPM chat` trong tài liệu lịch sử thuộc máy gốc.

## 2. Khôi phục source upstream và development

`openproject/upstream/` và `openproject/development/core/` được dựng lại thay vì commit bản vendor trùng lặp. Script dưới đây checkout commit chính xác từ lock, áp dụng patch riêng và chép source untracked được lưu:

```powershell
python scripts/restore_upstream.py
```

Lệnh cần Git/network. Nó từ chối ghi đè thư mục có sẵn và không sửa runtime. `core/overlay` và `development-patch` là hai biến thể khác nhau, không tự chép đè lên nhau.

## 3. OpenProject local

Đọc `openproject/README.md`, `openproject/VALIDATION.md`, các tham số của `Manage-OpenProject.ps1` trước khi dùng Setup. Script Setup có thể tạo Docker volumes, import dữ liệu demo và tạo tài khoản private trên máy mới. Chỉ thực hiện khi đó là mục tiêu của bạn:

```powershell
./openproject/Manage-OpenProject.ps1 -Action Setup
./openproject/Manage-OpenProject.ps1 -Action Start -LocalOnly
./openproject/Manage-OpenProject.ps1 -Action Status
```

Nguồn WBS CSV là dữ liệu bài tập, không chứng minh trạng thái hoàn thành thực tế. Không dùng `Restore -ReplaceLocalData`, xóa volume hay reset account như bước cài đặt thông thường.

## 4. AI và Telegram

Đọc `openproject/ai/README.md`, `CHECKPOINT.md` và `README_OPERATIONS.md`. Setup AI tạo môi trường, build image và cấu hình workspace; không đồng nghĩa Core đã rollout/được nghiệm thu. Cấp API key và đăng ký actor riêng, kiểm tra quyền trước khi bật ghi dữ liệu.

Telegram có `.env.example` riêng trong `openproject/ai/telegram-ai/`; copy thành file private ngoài Git rồi điền credential mới theo README của bot. Không dùng lại token của người khác. Chưa có cấu hình provider thì chạy offline tests trước; không cần gọi model thật để xác minh việc clone source.

## 5. Đồng bộ Git

```powershell
git pull --ff-only
git switch -c codex/my-change
# Sửa và kiểm tra đúng phạm vi
git add <file-da-xem>
python scripts/check_publication.py
git diff --cached --check
git commit -m "Describe the concrete change"
git push -u origin codex/my-change
```

Mở PR và merge sau khi check phù hợp đạt. Nếu `--ff-only` báo divergence, xem hai phía và merge có chủ đích; không tự reset hoặc force-push để bỏ thay đổi.
