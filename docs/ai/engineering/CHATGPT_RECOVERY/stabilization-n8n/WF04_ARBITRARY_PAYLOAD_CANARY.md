# WF04 storage redaction — synthetic canary

Ngày 2026-11-02, chạy image `qldapm-n8n:recovery-redaction-overwrite-candidate` trong container disposable với `--network none` và chỉ mount read-only thư mục này. [Kết quả](wf04-arbitrary-payload-canary-result.json): header Bearer được che; marker trong nested field và free text vẫn còn. Đây là **bằng chứng giới hạn của redactor**, không phải chứng nhận an toàn để bật retention.

Chạy lại trong PowerShell tại project root:

```powershell
docker run --rm --pull never --network none --mount 'type=bind,source=D:\AI project\QLDAPM chat\docs\ai\engineering\CHATGPT_RECOVERY\stabilization-n8n,target=/test,readonly' --entrypoint node qldapm-n8n:recovery-redaction-overwrite-candidate /test/wf04_arbitrary_payload_canary.js
```

Script chỉ dùng marker tổng hợp và kiểm tra trực tiếp `redactBundle`, không chạy WF04 hay scan persistent storage. Cùng phiên, `test_n8n_storage_redaction.js` và `test_n8n_persistence_overwrite.js` đều PASS trong image với `--network none`; test overwrite dùng mock DB và filesystem. Các test này chưa chứng minh persistence filesystem thật, restart, concurrency, hoặc visibility và correlation của WF04. Không thay đổi MAIN.
