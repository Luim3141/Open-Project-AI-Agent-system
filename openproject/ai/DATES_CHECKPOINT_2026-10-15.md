# Gemini nhận biết công việc và sửa ngày — 15/10/2026

## Đã sửa và triển khai staging18091/18092

User cung cấp ID và ngày đủ rõ. Các lỗi thuộc tool contract/intent guard/progress UI; không phải thiếu mô tả nghiệp vụ. Chỉ PM được sửa nghiệp vụ theo RBAC mới; không thay role, permissions, workflow, lịch làm việc, key/model/proof/quota hoặc live/Jira.

## Nguyên nhân có bằng chứng

1. Typed update tool, gateway, strict core mutation và preview chưa có start_date; mới chỉ có due_date.
2. Guard bỏ sót `set`, `thêm deadline`, reassignment `chuyển...BE...FE`; parser bỏ sót `subtasks112`/plural và danh sáchID. Run5a095514… của PM với câu set ngày442 bị AI_WRITE_ACTION_NOT_REQUESTED. Không chạy lại các lệnh nghiệp vụ cũ trên112/442.
3. Sau get_work_package, execution_report chưa có kết luận đã chèn câu “Chưa có dữ liệu…” và UI in nó khi run vẫn running. Câu đó là fallback của host, không phải kết luận Gemini đã phân tích thiếu thông tin.
4. Ngày10/10/2026 là thứ Bảy. Native form/PATCH điều chỉnh startDate sang12/10 theo lịch làm việc. Readback guard cũ coi khác biệt này là502 dù native write đã hoàn thành. Khi đặt mỗi dueDate, native còn có thể tính startDate từ duration đã lưu.
5. ProviderError merge từng dùng HTTP503 đè semantic run status; đã tách provider_http_status.

## Thay đổi

- Nullable start_date/due_date có trên typed schema, catalog, gateway validation/native mapping, strict Ruby allowlist, before/after preview và receipt. Dates dùng ISO YYYY-MM-DD; model được hướng dẫn hiểu DD/MM/YYYY, chỉ hỏi thêm khi thật sự thiếu.
- Cả hai ngày được gửi trong một update; ngày sai/range start>due bị từ chối trước ghi. Native form preflight tính ngày canonical, giữ validation và native permissions. date_adjustments ghi rõ requested/actual, kể cả ngày tự tính do duration. Preview và kết quả hiển thị ngày thực tế cùng lý do; không tự đổi ignoreNonWorkingDays hoặc retry để ép ngày nghỉ.
- Intent nhận set/thêm ngày/thêm deadline/lên lịch/chuyển role, ID-colon; ID parser nhận Task(s), Subtask(s), Ticket(s), Epic(s), ID và danh sách dấu phẩy/và/and. Comment bodies và quoted read text không tự mở rộng quyền.
- Running progress không hiển thị câu kết luận thiếu dữ liệu; native receipts vẫn giữ. HTTP error status không đè trạng thái kết quả.
- PM-only-write, target scope, checkbox consent, lock version, native readback và unknown-write stop giữ nguyên.

## Nghiệm thu thực tế

-147 Windows unit/regression PASS; Linux147 tests gồm143PASS+4OS-only skip. artifacts/dates-unit-final.log và dates-linux-final.log.
- Native PM date pair, clear both dates, invalid date/range/no write,4non-PM roles denied PASS. Dùng đúng hai fixture444/445; toàn bộ333 source fields/version trước thử giữ nguyên.
- Gemini thật câu `set ngày bắt đầu và ngày kết thúc cho task445 ...10/10/2026...31/12/2026` → một update có cả hai ngày; native start12Oct/due31Dec, receipt giải thích native calendar; run0464343f-14c1-40b7-aab6-aefee07285a8.
- Gemini thật `thêm deadline cho subtask445 ...31/12/2026` → tool chỉ gửi due_date; native đúng deadline và tự tính start theo retained duration; rune526b92c-51d6-48df-a6da-4aa72254974a. Harnesstest ban đầu kỳ vọng start vẫnnull là giả định sai về scheduling; đã sửa, không replay inference.
- Browser thật `set ngày bắt đầu15/10/2026 và deadline30/11/2026 cho subtasks445...chỉ tạo đề xuất` → nhận đúng hai fields, bảng trước/sau đúng, không ghi. Run01a2b960-201d-48d3-a64c-c539a660dc6d; proposal2c76406c-ae55-4174-88b5-4ea25b27a0d6 đã từ chối trênUI, native dates giữ nguyên.
-2 native UI cases PASS: hide in-progress fallback, preview cả ngày bắt đầu/hạn và calendar adjustment. artifacts/dates-ui-final.log. Full legacy UI gate suite có4ca kỳ vọng BE được thao tác gate không còn phù hợp PM-only policy; không tuyên bố full old UI/gate suite PASS.
- Source/image parity cả core/gateway PASS; artifacts/dates-image-parity.json.
- Cleanup chính xác444/445 PASS. Cleanup lần đầu bị từ chối đúng vì stage-owner không phải PM; đã dùng đúng PM author của các fixture như harness RBAC hiện có, kiểm tra ID/SourceID/author/no-children; không nâng quyền.
-333 bản ghi baseline vẫn khớp; user tạo thêm446 trong lúc nghiệm thu, được giữ lại. Hiện 334 bản ghi. Không dùngbaseline329/330 cũ để xóa dữ liệu người dùng.
- Restart gateway PASS: usage/circuit/recovery/requests/runs/proposals fingerprints và private config/credentials/key giữ nguyên. Ledger455 history tại restart; giữ nguyên local90%13RPM/225000TPM/450RPD. Đây là history count, không phải rolling24h count. Gemini authorized; live images2bee/7190 unchanged. artifacts/dates-restart.json.

## Phần kiểm thử không thực hiện

Automatic approval review chặn lệnh ghép gọi Gemini và tự xác nhận preview quaAPI; output chỉ ghi blocked by policy, không cung cấp lý do. Không bypass bằng đường khác. Đã dùng đường an toàn hơn: tạo/đọc preview trênbrowser rồi từ chối. Chưa kiểm thử lại thực thi bước duyệt quaAPI trong lượt này; không chạy thêm Gemini reassignment acceptance. Việc ghi date pair đã được chứng minh qua native và Gemini thật ở trên.

Chưa production qualification/live rollout. Fork có sẵn các thay đổi RBAC chưa commit từ trước; giữ nguyên, chỉ đồng bộ3file overlay liên quan vào fork, không commit/stash/reset công việc khác.

## Runtime / rollback

Core sha256:1cdd2590d6f31384eacf93bd504b421288c7d0a7ef37a137e1e2b8ec009dd87a
Gateway sha256:79bc0c4c67d606b79936a7324040a7543c1b00a4518337a3e9270af0cc62ff3e

Backup private %LOCALAPPDATA%/QLDAPM/openproject-ai/operator/dates-20261015-1792047925 và dates-final-20261015-1792048443. Originalpair4f62898f…/1b59ea4d… giữ trênhost. Rollback imagepair/lock nếu cần, giữ DB/ledger/receipt HIỆN TẠI; không restore state cũ hoặc chính sách non-PM-write đã superseded.

Source: gateway/catalog.py,service.py,presentation.py,gemini.py; core helper/mutations/result template; exports; tests/test_dates.py,test_level2.py,core/ui_commands_test.rb,tests/stage_dates.py. architecture.md và BUSINESS_COMMANDS.md đã cập nhật. Source333baseline và3realrun receipts trong artifacts/dates-stage.json; không chạy lại harness trênmanifest đã cleanup.

## Giới hạn nhận biết còn thật

Mỗi run gửi câu lệnh hiện tại, không tự ghép toàn bộ hội thoại cũ làm ngữ cảnh. Với sửa trực tiếp, ghi ID rõ và yêu cầu trường cần đổi; bật checkbox nếu muốn thực hiện ngay. Mặc định tạo proposal. Gemini đọc ticket/business context theo quyền, không tự có quyền PM. Lịch ngày làm việc/duration và quota/time/resource bounds vẫn áp dụng; không giới hạn số thao tác cố định6.

Ảnh: artifacts/dates-success-browser.png (native-confirmed pair/calendar), dates-preview-browser.png (hai fields trước/sau). Lượt lỗi lịch sử được giữ để audit, không tự đổi thành success hoặc tự gửi lại.
