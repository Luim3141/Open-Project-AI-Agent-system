# Tài khoản các role còn lại —15/10/2026

User yêu cầu cấp toàn bộ tài khoản các role còn lại trong dự án hiện hành staging18091. Readonly native kiểm tra project3/qldapm-local, membership/role/active/admin flag và password hash với update_legacy:false.4accounts active/nonadmin/passwordvalid:6 ba-pm (QLDAPM BA-PM),7 pm (QLDAPM PM),9 fe (QLDAPM FE),10 qa (QLDAPM QA); cả4force_password_change=true. Không tạo/reset tài khoản hoặc đổi quyền/token/session.

BE8/loginbe đang dùng mật khẩu user đã đổi; bootstrap cũ không khớp. Giữ nguyên, không xuất mật khẩu bootstrap sai. Existingadmin11/luim-admin vàstage-owner không bị thay đổi. Nativecheck không đăng nhập thay user và không bypassMFA/first-password-change.

File thông tin4role/password hiện có nằm private ngoàiGit `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/access/project-roles-18091.credentials.txt`; ACL chỉ LUIM\LUIM vàSYSTEM. Không đọc secret vào chat/log/source/screenshot. User tự đăng nhập và đổi mật khẩu khi được yêu cầu. CredentialsJSON/token/environment không được cung cấp. Metadata proof `artifacts/role-access-18091.json`; backend/live/Jira/Gemini/source329/images không thay đổi. Khi resume không tự reset mật khẩu đã được user đổi; kiểm tra riêng từng account trước khi tái dùng bootstrap.
