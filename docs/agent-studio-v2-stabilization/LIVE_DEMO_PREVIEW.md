# Phạm vi live E2E đề xuất

Read-only preflight: base catalog2units +11extra definitions =13; `gateway/engineering_planning.py` có `MAX_ENGINEERING_UNITS=13`, `feedback_base_unit` từ chối unit mới khi đủ13. Không xóa unit cũ hoặc replay391/397 để vượt giới hạn.

Đề xuất duy nhất cần Owner chốt: tăng catalog ceiling13→14 để thêm đúng1demo Task mới, chỉ bổ sung regression tests cho HTTP methods bị từ chối trên `/healthz` trong mini-task-manager. Không đổi hành vi app; không merge/deploy. Dùng BA/PM/Dev/Reviewer/QA và runner/model/key/budget hiện có, không thêm orchestration. Giữ nguyên call caps, quota gates, Native permissions và completion gates. Task chỉ cần đi tới runtime terminal/READY FOR RELEASE, không tự duyệt DONE.

Ảnh hưởng: có thêm1unit/Task/run records và artifacts thật; ceiling14 cần được giữ để không làm catalog14records vi phạm schema sau test. Rollback không được xóa dữ liệu mới để quay lại13. Code diff dự kiến chỉ constant giới hạn và boundary regression; không thực hiện trước khi Owner duyệt. Stabilization UI/read path tiếp tục độc lập.
