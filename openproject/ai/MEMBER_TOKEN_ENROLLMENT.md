# Owner enrollment PM/BA — 2026-10-09

Phạm vi: chỉ cấp credential PM/BA theo yêu cầu owner. Không deploy, đổi image, restart, chỉnh workflow, thay password/TOTP hoặc tác động Jira. Không tiếp tục rollout của tác vụ khác.

## Kết quả đã kiểm chứng

| Kiểm tra | BA-PM 19 | PM 20 |
| --- | --- | --- |
| Active, không admin, đúng role/project 5 | PASS | PASS |
| API token qua APITokens::CreateService của live 17.9.1 | PASS | PASS |
| API v3 users/me và project membership | PASS | PASS |
| Đăng ký qua manage_local.register | PASS | PASS |
| REST identity đúng người dùng | PASS | PASS |
| MCP HTTP initialize/list tools/identity/analyze | PASS | PASS |
| MCP stdio initialize/list tools/identity | PASS | PASS |
| Đọc 329 work package | PASS | PASS |
| Bearer hash đúng user/role, không revoked, TTL 24h | PASS | PASS |
| Credential/Bearer ACL chỉ LUIM và SYSTEM | PASS | PASS |

Rails transaction có assert bảo toàn toàn bộ API token đã có và attributes của user/TOTP devices 19/20/21 trước/sau. Không tự chuyển trạng thái công việc. Token native được lưu hashed theo model OpenProject; bản cần dùng bởi Gateway được lưu private ngoài Git.

BE21: active, không admin, role QLDAPM BE, quyền view/edit work packages đã kiểm tra backend. Chưa cấp token BE vì phạm vi cấp là PM/BA; API/MCP với danh tính BE **NOT TESTED**, không dùng token PM/BA để giả nghiệm thu BE.

## Bảo mật và trạng thái UI

PM/BA/BE vẫn yêu cầu đổi password tạm, chưa có TOTP device. API token là credential riêng, không yêu cầu OTP cho mỗi API request; không chứng minh người dùng đã đổi password hoặc đăng ký TOTP. Không khóa/unlock hay thay thiết lập xác thực.

Proxy UI 8088 có maintenance nên trả503. Giữ nguyên maintenance. Owner helper đọc API v3 qua Gateway container và network Docker hiện có, vẫn dùng native authentication/authorization. REST/MCP local tại `http://127.0.0.1:8090`; không mở tunnel hoặc cổng mới. MCP remote và web login/TOTP **NOT TESTED** trong tác vụ này.

Private runtime: `%LOCALAPPDATA%/QLDAPM/openproject-ai`. Bearer theo người nằm ở `operator/user-19.token` và `operator/user-20.token`; native credentials ở `gateway/credentials.json`, bản lưu enrollment ở thư mục `operator/enrollment-*`. Không paste nội dung các file vào chat/log hoặc đưa vào Git. Native API token không có TTL do helper này thiết lập; Bearer Gateway hết hạn24h nhưng native key vẫn cần được owner quản lý riêng.

Chỉ bản token tạm `/tmp/qldapm-issued-d28682ab70304acd9e1902143afb8320` trong container đã được xóa sau đối soát; bản host private giữ lại, không thu hồi token.

## Lệnh kiểm tra lại an toàn

Trong PowerShell, từ `D:/AI project/QLDAPM chat/openproject/ai`:

```powershell
./.venv/Scripts/python.exe provision_member_tokens.py verify
./.venv/Scripts/python.exe -m unittest tests.test_member_enrollment -v
```

`enroll` chỉ dành cho enrollment mới và từ chối nếu đã có mapping/Bearer/token row. `resume PRIVATE_DIRECTORY` chỉ tiếp tục file enrollment nằm trong private operator runtime; credential đã đăng ký phải khớp, nếu khác thì từ chối, không ghi đè. Không chạy đồng thời với Register khác. Token hết hạn không được helper tự thay/thu hồi; dùng quy trình owner riêng sau khi xác định phiên đang dùng.

Bảy unit tests PASS: enrollment mới, giữ mapping/Bearer/token row, không lộ output Docker lỗi, backend enrollment chỉ GET, từ chối private path sai, resume không thay native credential có sẵn. Live MCP dùng danh tính PM/BA thật, không credential staging.

Đăng ký lại cùng private enrollment đã PASS đối soát giữ nguyên cả native mapping và bytes của hai Bearer. REST OpenAPI và MCP từ chối thiếu Bearer401; OpenAPI từ chối Bearer sai401. Quét logs20phút gần nhất của live web và Gateway bằng giá trị secret trong bộ nhớ: không có native token/Bearer đã cấp, PASS; không xuất nội dung logs hoặc secret ra terminal. Không khẳng định đã kiểm tra mọi log/lịch sử trên toàn host.
