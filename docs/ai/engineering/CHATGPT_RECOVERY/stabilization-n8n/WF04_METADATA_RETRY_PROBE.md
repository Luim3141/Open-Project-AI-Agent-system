# WF04 metadata-only: retry gate

Ngày 2026-11-02, `wf04_metadata_retry_probe.js` gọi `ExecutionService.retry` thật của image `qldapm-n8n:recovery-redaction-overwrite-candidate` trong container `--network none`. Persistence và workflow runner là stub; input chỉ chứa synthetic marker. Kết quả: metadata-only không có `data.executionData` bị `AbortedExecutionRetryError` trước runner; control có payload chuyển marker đến runner. Đây là unit probe trong container, không phải clone WF04 end-to-end, restart hoặc concurrency.

```powershell
docker run --rm --pull never --network none --mount 'type=bind,source=D:\AI project\QLDAPM chat\docs\ai\engineering\CHATGPT_RECOVERY\stabilization-n8n,target=/test,readonly' --entrypoint node qldapm-n8n:recovery-redaction-overwrite-candidate /test/wf04_metadata_retry_probe.js
```

Tra `workflowId` theo `executionId` trong cùng transaction có thể là hướng cho legacy routing nếu kiểm tra được row, version-lock mọi hook và fail closed; vẫn phải xử lý create, partial/full overwrite, concurrent updates và mọi persistence surface. Routing không giải quyết xung đột: retry của n8n cần execution state và workflow snapshot; metadata-only không chứa arbitrary input để khôi phục chính xác. Một nguồn replay an toàn, có kiểm soát truy cập và được chứng minh tương đương có thể thay đổi kết luận, nhưng chưa được xác minh cho WF04.

Không triển khai candidate hoặc thay đổi MAIN. Chưa chứng minh success/error, restart, concurrency, visibility hay correlation của giải pháp metadata-only. WF04 retention tiếp tục BLOCKED.
