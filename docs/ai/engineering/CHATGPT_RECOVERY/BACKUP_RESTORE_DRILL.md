# Isolated restore / code rollback drill

Hiện hành: `phase2-20261101T050128Z/`. Mọi đường dẫn evidence dưới đây tính từ thư mục CHATGPT_RECOVERY. SOURCE_FIXED/CANDIDATE_TESTED không đồng nghĩa DEPLOYED_TO_MAIN/LIVE_INTEGRATION_VERIFIED/OWNER_ACCEPTED.

**BACKUP_RESTORE_VERIFIED.** Backup gốc `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\operator\chatgpt-recovery-20261101T043043Z`; PG custom dump signature/TOC đã kiểm, full restore vào PostgreSQL17.11 trên internal Docker network riêng, không shared MAIN volumes/ports. Restore221public tables; Project5=341WP/maxlock4; Project6=7WP/maxlock9; WP379=project6/status7/lock4. Bảng và row-count chi tiết: `phase2-20261101T050128Z/restore-drill-result.json`.

gateway.sqlite41tables và knowledge.sqlite9tables được copy private, schema và toàn bộ table row counts bằng backup, integrity_check=ok. Engineering receipts/history được đối chiếu qua table counts; không suy count thành outcome correctness. Đây là backup sau WP385 deletion, không chứa record385 và không phục hồi lịch sử đã mất.

Phase2 Core candidate còn được restore/startup lần nữa, tạo replacement bằng official Native API trên clone, read-back parent/project/relation, Project5 fingerprint giữ nguyên. Rollback Core r24 cũng startup healthy trên fresh restored clone. Gateway candidate và rollback r24 đều actual Uvicorn health200 trên network none, no live/private mounts. Gateway startup dùng empty fixture state, không phải diễn tập full live config/traffic cutover. N8n candidate startup và storage canary có drill riêng; chưa restore MAIN n8n history vào clone.

Cleanup chỉ label/UUID-owned disposable resources. main_native_clone kiểm container IDs/images/starttimes trước/sau mỗi drill; không restore đè MAIN. Logs lỗi đầu (fixture Host thiếuport; relation POST saiendpoint) giữ nguyên, lần cuối đã đạt; không đếm lỗi thànhPASS.

Source recovery: private local Git `27db752d686d86b9683e7e7a6b15f6a223f48939`,587allowlisted files,1credential-shaped test fixture quarantined. Root repo2tracked/no remote vẫn giữ nguyên. Private Git bundle verified; dependencies/requirements và Docker recipes được version, immutable runtime bases lưu private archive theo base-image-archive.json. Image build dùng snapshot commit307503c; qualification commit mới chỉ thêm host delivery/adapter/tests/architecture,15packaged files vẫn khớp. Không remote/push. Cần backup mới ngay trước approved cutover nếu dữ liệu đã đổi; không dùng backup này rollback business DB cũ lênMAIN.

Artifact hygiene:9 file Native clone tạm (gồm dump) đã được chuyển khỏi workspace sang private operator root; manifest chỉ lưu path/hash/size ở private-native-artifacts.json. Không có DB file trong source Git bundle. native_recovery_drill.py hiện luôn đặt clone output ở private root.
