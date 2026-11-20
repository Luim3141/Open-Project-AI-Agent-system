# Historical AI migration — chưa import

Trạng thái: **BLOCKED_MAPPING_SENSITIVITY_AND_PROVENANCE**,0import,0replay,0businesswrite. Main local execution mới không phải dữ liệu Stage được promote.

23records trong manifest hiện có được giữ làm baseline. Stage `ba-pm`/6 là BA-PM trong khi Main `ba-pm`/19 là PM; Stage `pm`/7 là PM trong khi Main `pm`/20 là BA. Vì vậy map theo login làm đổi thẩm quyền/ownership cho13records. Các map8→21(BE),9→22(FE),10→23(QA) không có xung đột role nhưng vẫn cần review nội dung và provenance.

Image giống nhau không đủ điều kiện import. Monitor hiện revalidates Native references và dùng actor/project isolation, trong khi Stage history không có14event stream như run Main mới. Không được tạo events giả, đổi created timestamps, copy receipt thành Main provider request hoặc replay historical tools.

Phương án nhỏ nhất đề nghị: giữ Stage là nơi đọc lịch sử gốc; nếu Owner cần archive Main, thêm storage namespace archive chỉ đọc, explicit source environment/project/actor/run/receipt hashes, mapping do Owner duyệt và citations đánh dấu historical. Archive không nhập vào live execution tables, không tính usage/metrics Main. Chỉ chuyển bản được phân loại/lọc secrets sau backup và clone tests chống duplicate/cross-actor/cross-project. Chưa có importer được qualification hoặc phê duyệt chuyển dữ liệu nhạy cảm; chưa triển khai phương án này.

Owner phải quyết định có thực sự cần archive Main và map ownership nào trước khi thực hiện. Bước này tuân theo mụcIV/VII của takeover; không cần xoay key/TOTP hoặc ghi đè database để hiển thị history.
