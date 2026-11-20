# TOTP recheck — chỉ đọc, 18Oct2026 10:50 ICT

**Quyết định Owner: NOT_APPROVED_DO_NOT_ROTATE.** Không tạo, hủy kích hoạt hoặc xoay vòng thiết bị; không đổi mật khẩu, role, Main hoặc Quick Tunnel. Đây là đối chiếu độc lập lần hai theo yêu cầu Owner, không phải thực hiện remediation.

## 1. Tài liệu đã đọc đầy đủ trong lượt này

- verification_runs/run_20261018_0515/TOTP_ROTATION_EXECUTION_PROOF.md
- verification_runs/run_20261018_0515/DEFECT_REGISTER.md
- verification_runs/run_20261018_0515/FINAL_OWNER_APPROVED_EXECUTION_REPORT.md
- takeover_20261018_1035/SECURITY_REMEDIATION_PREVIEW.md

Ba báo cáo Wave6 khẳng định old23–28 inactive và new35–40 active/default; stage-owner user13. Preview của Codex dựa trên kết quả truy vấn ở lần tiếp quản trước, chưa thực hiện thao tác nào. Mã băm tài liệu và log được lưu trong wave6-evidence-sha256.json; không ghi đè hồ sơ Wave6.

## 2. Kết quả PostgreSQL mới và Rails thực tế

| Login | User ID thực tế | Device ID active | active | default |
|---|---:|---:|---|---|
| ba-pm | 6 | 27 | true | true |
| pm | 7 | 24 | true | true |
| be | 8 | 23 | true | true |
| fe | 9 | 25 | true | true |
| qa | 10 | 26 | true | true |
| stage-owner | 5 | 28 | true | true |

- Thiết bị23–28: **6/6 tồn tại, 6/6 active** và cả6 default=true.
- Thiết bị35–40: **0/6 tồn tại** trên DB này.
- User13: **không có bản ghi**. Login stage-owner hiện thuộc **User5**, admin=true. Đây là nguồn của cách ghi user5 của Codex, không phải rename hay chuyển tài khoản.
- Trong sáu tài khoản này, mỗi người có đúng một active/default device, không có hai default xung đột.
- File khóa private đã lưu khớp các thiết bị cũ tương ứng (chỉ xuất boolean/IDs, không xuất secret/OTP).

Hai đường kiểm tra cùng SQL:
1. psql trong qldapm-ai-stage-db-1, PGOPTIONS default_transaction_read_only=on.
2. ActiveRecord::Base.connection của Rails runner trong qldapm-ai-stage-staging-web-1, cũng bắt buộc read-only. Đây là Rails connection thật, không chỉ suy đoán từ DATABASE_URL.

Cả hai báo transaction_read_only=on; trùng database openproject, database OID16384 và cluster system_identifier **7694597024125386790**. Toàn bộ users/devices trả về giống nhau. psql qua Unix socket nên inet_server_addr=null; Rails dùng TCP172.27.0.2. Sự khác biệt giao thức này không phải khác database.

Bằng chứng: postgres-direct.json, rails-actual-connection.json và result.json. Câu SQL đầy đủ trong recheck.py chỉ SELECT; không gọi OTP.verify_token, save!, update, rotation hoặc login.

## 3. Loại trừ sai Compose/project/image ở lượt kiểm tra hiện tại

Docker context desktop-linux, Docker Desktop. Container DB0775f1163e68 và Web0422a1d53442 đều có label project=qldapm-ai-stage, service=db/staging-web. Web endpoint db:5432/openproject, DB volume qldapm-ai-stage_stage-db; IP DB trên stage network khớp Rails172.27.0.2. Web image8a42c7ef; Gateway006b9c6c; Tunnel candidate. Toàn bộ tên/ID đầy đủ/image/network/mount/config files có trong target-identity.json.

Container Main thuộc project khác không được dùng để truy vấn. Các restore/qualification DB khác đang stopped không được khởi động hoặc truy vấn. Image, StartedAt và RestartCount của năm container đã chọn không đổi so với đầu takeover (preservation.json). Cấu hình hiện tại đúng tên target được chính báo cáo Wave6 chỉ định.

Không thể suy ra toàn bộ lịch sử từng DB từ trạng thái hiện tại. Chưa có chứng cứ cho thấy một rotation thành công rồi bị rollback, hoặc thành công trên DB khác; cũng không khẳng định điều đó chưa từng xảy ra. Với target đang phục vụ, dữ liệu hiện tại chắc chắn không khớp báo cáo35–40/user13.

## 4. Đối chiếu raw logs Wave6

- logs/totp_rotation_execution.log ghi NEW_DEVICE_VERIFY_FAILED: ba-pm và stack trace; không phải log thành công sáu tài khoản.
- logs/old_devices_deactivation_check.log ghi cả sáu thiết bị cũ true/true. Dòng stage-owner cũng ghi device28 nhưng không cung cấp bằng chứng user13.
- Browser log cho thấy PM/FE đăng nhập được từ file secrets. Nó không tự xác nhận age/deviceID của key; phép so sánh private key ở lượt này cho thấy file hiện khớp thiết bị cũ.
- Source operator chỉ cập nhật/sau đó lưu credentials sau các bước rotation; source có nhánh thoát khi Rails lỗi. Không chạy lại source này. Lỗi time-window trước đây nêu trong preview chỉ là giả thuyết cần kiểm thử, chưa phải root cause được xác nhận.

Không có raw SQL hay success receipt35–40 trong các bằng chứng vừa đối chiếu để giải thích con số13/35–40 ở phần báo cáo cuối. Do đó giữ trạng thái **DEF-08: CONTRADICTORY_EVIDENCE / NOT_VERIFIED_ON_CURRENT_STAGING**, không xác nhận FIXED_AND_VERIFIED từ markdown.

## 5. File secrets và HTTP

File C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/secrets/staging_totp_secrets.json tồn tại,1011bytes. Không còn file cùng tên trong access/. ACL hiện chỉ LUIM\LUIM và SYSTEM FullControl, kế thừa từ parent (Protected=false). Kiểm tra mounts của các serving containers không thấy thư mục/file secrets bị mount vào web root. Các field hiện có user/pass/role/totp_secret; không có device_id chứng minh35–40. Không xuất nội dung file.

Public login200. Hai đường dẫn /staging_totp_secrets.json và /secrets/staging_totp_secrets.json trả404. Đây là kiểm tra những đường dẫn cụ thể cộng với mount isolation, không phải cam kết đã thử mọi URL có thể có. Xem secret-file-metadata.json, secret-file-acl.json và http-recheck.json.

## 6. Quyết định và tác động

Giữ nguyên toàn bộ thiết bị hiện tại theo yêu cầu Owner. Không xin lại phê duyệt trong lượt kiểm tra này. Đóng băng preview ở trạng thái NOT_APPROVED; chỉ tiếp tục điều tra chỉ đọc nếu cần.

Rủi ro thực tế: các key cũ được báo cáo đã lộ vẫn đang được DB chấp nhận; đổi vị trí file không đồng nghĩa đã thu hồi key. Nếu sau này Owner cân nhắc remediation, tác động/cách phục hồi đã có trong preview: sáu người enroll lại TOTP, backup Staging trước, xác minh key/đường đăng nhập mới và private recovery mapping trước khi thu hồi key cũ; không đổi password/role/Main/tunnel, không rollback sang key đã lộ. Chưa thực hiện bất cứ bước mutation nào.

## 7. Sự cố lọc đầu ra

Một lần đọc source của operator đã hiển thị các mật khẩu hardcode có sẵn trong tool output. Codex đã thông báo lỗi lọc này, không lặp lại giá trị, không ghi chúng vào báo cáo mới và không tự đổi credentials. Các kiểm tra sau chỉ xuất field allowlist và kết quả so sánh boolean/IDs; raw secret/OTP không được ghi vào bộ evidence này.
