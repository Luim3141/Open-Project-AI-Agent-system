# WP385 / historical verdict recovery proposal

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

Kết luận pháp y vẫn như WP385_FORENSICS.md: WP385/journal1091/relation357 đã bị xóa; run b1cca031 forced succeeded mâu thuẫn raw agent FAILED và planning-knowledge checkpoint lỗi. Không tìm thấy Main backup trong create-delete window. Phase2 kiểm archive_mode=off/archive_command disabled, không có configured archived WAL/PITR được xác minh. Không khẳng định mọi backup ngoài máy/VSS đều không tồn tại.

Chọn **replacement WP mới bằng Native API**, không INSERT id385/resetsequence/created_at giả. Proposal cụ thể `phase2-20261101T050128Z/wp385-replacement-preview.json`: Project6/parent379; original plan/unit forensic reference; AC10 category POST/PATCH, AC11 category filter, AC12 CSV; dependency WP384. Trước MAIN write phải search exact plan+unit forensic marker trongProject6, không có duplicate mới create; nếu ambiguous/timeout thì dừng/read-back, không blind repeatPOST. Fresh Native role/project/parent lock/type options phải còn hợp lệ. Không gán acceptance/Done.

Clone thử bằng user20 nonadmin với token chỉ tạo trong disposable DB: POST /api/v3/work_packages trả201, ID clone387 (MAIN chưa có ID này do tác vụ), GET read-back project6/parent379; POST /api/v3/work_packages/<new>/relations + GET relation xác minh follows384. Original385 vẫn absent; Project5 fingerprint không đổi. Script native_recovery_drill.py có CLONE_ONLY guard, không là Main apply script. Log lần đầu wrong relation endpoint fail được giữ; lần cuối đúngAPI đạt.

Historical run: production source chỉ thay owner-facing projection khi persisted succeeded + agent FAILED/CANCELLED → blocked/RECONCILIATION_REQUIRED, giữ persisted_status và raw stored values. Test2cases nằm trong182suite. Đây là phát hiện mâu thuẫn, không phải kết luận đã chữa planning knowledge. Correction đề nghị sau Owner duyệt: append audited reconciliation note gắn original hashes/checkpoint/raw receipts, nêu actual partial plan publication và failed knowledge step; giữ mọi raw record. Không UPDATE status SQL, không tự retry unknown, không recredit success. Rebuild unit mapping/knowledge chỉ sau replacement được duyệt và read-back, để original385 mapping trong evidence.

**MAIN DATA APPROVAL PENDING.** Replacement và audited correction tách khỏi code rollout. Không có record/history nào đã được phục hồi trênMAIN trong batch này.
