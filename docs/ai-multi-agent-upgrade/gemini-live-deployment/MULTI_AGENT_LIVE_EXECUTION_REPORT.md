# Thực thi Multi-Agent thật

Thời điểm: 2026-10-19T07:24:51.120587+07:00. Trạng thái: **GEMINI_LIVE_STAGING_VERIFIED**.
Staging Gateway `sha256:40cb4806edd9c415bfb507a6c287c112283609f66263230e10cac242354e9a80`; Core `sha256:3b09393d123464a7baf4726daf69806de4754a0b1911173e6dbe58ecb3ac2f99` giữ nguyên.
Truy cập: [https://therapeutic-price-various-marking.trycloudflare.com](https://therapeutic-price-various-marking.trycloudflare.com); lấy lại Quick Tunnel URL tại [landing local](http://localhost:18090).
Billing: **BILLING_CONFIGURATION_UNCHANGED — OWNER_ATTESTED**. Đây là xác nhận của chủ dự án, không phải kiểm tra mới từ Google Cloud Console hoặc cam kết chi phí tuyệt đối bằng 0.


| Ca | Role / actor | Execution ID | Model calls | Kết quả mới nhất | Evidence |
|---|---|---|---:|---|---|
| A | PM / 7 | 322d10da-c17f-4724-a8f9-fe71ae2e43d7 | 1 | PASS | live-web-uat-retest.json |
| B | BA-PM / 6 | b9c5bfbe-9659-446c-b92a-94fa48b77528 | 1 | PASS | live-web-uat-retest.json |
| C | QA / 10 | 603a991e-fbd7-4743-aff6-443508c2500c | 1 | PASS | live-web-uat-retest.json |
| D | PM / 7 | 7d528511-c957-40b1-bd1e-c6fe7dd28650 | 4 | PASS | live-web-uat-final.json |
| BE | BE / 8 | 94473b2c-5eb8-4373-94ef-fe6e6d03375e | 1 | PASS | live-web-uat-final.json |
| E | FE / 9 | Admission denied | 0 | PASS | live-web-uat-final.json |
| FBA | BA-PM / 6 | Admission denied | 0 | PASS | live-web-uat-final.json |

A=PM Sprint/rủi ro; B=BA yêu cầu/AC trên10 Native assigned IDs; C=QA testcases cho38; D=PM cross-domain BA/Developer/QA cho38; BE=Developer rủi ro kỹ thuật; E=FE và FBA=BA mutation denied trước provider.

Ca D `7d528511-c957-40b1-bd1e-c6fe7dd28650` có một Gemini ModelPlan và3 specialist generateContent thành công HTTP200, đúng model; dependencies BA→DEV→QA→local Reviewer, aggregate3525 ký tự được đọc từ receipt hiển thị trên Web và chụp riêng. Usage/receipt IDs thực tế nằm trong [live-web-uat-final.json](run_20261019_0013/live-web-uat-final.json); không chỉ dựa vào trạng thái backend.

A/B/C đã gọi trên image7ffee; sau đổi receipt bookkeeping và capoutput, cả3 kết quả được mở lại và xác minh trên UI/image cuối40cb4806 không gọi lại model. D/BE/E/FBA chạy trên1c4ac606; toàn bộ saved results và5roleUI được mở lại trên40cb4806 sau ACL-only fix. SDK/live_agents.py không đổi hash, không gọi lại Google sau sửa readback. Xem [final-ui-checks-acl.json](run_20261019_0013/final-ui-checks-acl.json). Không tuyên bố mọi model attempt đều chạy trên cùng một image.

Context: Native API với actor hiện hành, tối đa10 inputs, assigned-to-current-actor nếu nonPM không chỉ ID; description/comments giới hạn và lọc dữ liệu. PM nhận Native Sprint/project options. Second Brain chỉ actor/project/current version và IDs thuộc input. Clone contract đã quan sát Sprint+knowledge projection trước khi fixture đổi version; Native451 đổi version thì retrieval cũ không còn được đưa vào. Serving PM indexed38 hợp lệ, 4 tài liệu cũ được giữ +1 tài liệu/3chunks mới; readback hiện tại trả1 hit. [live-context-readback.json](run_20261019_0013/live-context-readback.json) là tái dựng read-only đường context sau lượt chạy, không phải bản sao prompt đã gửi Google.

Đã có7 analysis workflows thành công,3 analysis attempts lỗi giữ nguyên lịch sử; các ca bị chặn RBAC không gọi model. 19 generation attempts toàn phiên kể cả smoke và response invalid; không che lỗi bằng deterministic fallback hoặc fake LIVE_SUCCESS.

## Bổ sung ACL readback cuối — 2026-10-19T07:24:51.120587+07:00

Gateway40cb4806 mang context fingerprint qua progress/notify/failure, revalidates Native ACL/version cả partial output. Regression RED→GREEN;178Windows/63LinuxPASS. Hai legacy failedpartial không đủ source proof nay trả STALE, nội dung không lộ; raw history giữ. Saved LIVE_GEMINI outputs vẫn hiển thị qua5roleUI thật. [ACL API evidence](run_20261019_0013/acl-live-readback.json); [Gateway-only deploy](run_20261019_0013/acl-fix-deployment-receipt.json). Không thêm Googlecalls (vẫn19), không đổi successful generation modules. PMapprove trênclone/providerMOCK đã thử trước ACL-only fix trên1c4; latest40cb clone contract read/preview PASS, không ghi fixture lần nữa.
