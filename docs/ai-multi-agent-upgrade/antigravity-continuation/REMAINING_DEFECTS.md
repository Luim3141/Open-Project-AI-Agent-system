# DANH MỤC CÁC VẤN ĐỀ TỒN ĐỌNG, KỸ THUẬT NỢ VÀ QUYẾT ĐỊNH CHỜ DUYỆT
## REMAINING DEFECTS, TECHNICAL DEBT & PENDING OWNER DECISIONS

- **Thời điểm rà soát:** 2026-10-21T11:51:00+07:00
- **Nguyên tắc báo cáo:** Minh bạch tuyệt đối, không che giấu khiếm khuyết, tuân thủ nguyên tắc Ponytail & Superpowers.
- **Trạng thái tổng thể mã nguồn:** **0 LỖI CHỨC NĂNG TỒN ĐỌNG TRÊN BỘ CODE CANDIDATE V2 (81/81 TESTS PASS)**.

---

## 1. DANH MỤC ĐIỂM NGHẼN VẬN HÀNH (OPERATIONAL BLOCKERS)

Các vấn đề dưới đây không phải do lỗi code, mà xuất phát từ cơ chế rào chắn an toàn (Safety Gates) nhằm bảo vệ tính nguyên vẹn của hệ thống Main:

| Mã Điểm Nghẽn | Hạng Mục | Mô Tả Thực Tế | Mức Độ | Trạng Thái Hiện Tại | Hành Động Tháo Gỡ Cần Thiết |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **BLK-01** | **Main Gateway Runtime Parity** | Main Gateway (`qldapm-ai-gateway-1`) đang chạy image cũ `456c38f6a9a9`, chỉ phân tích được `['ba', 'reviewer']` và thiếu tác tử `qa` khi chạy câu lệnh Approval B. | **CAO** | `BLOCKED_ON_MAIN_RUNTIME_DEPLOYMENT` | Chủ dự án phê duyệt triển khai image candidate `qldapm-ai:rd-qual-20261021-v2` lên service Gateway của Main. |
| **BLK-02** | **Main Work Packages Schedule Write** | 329 Work Packages trên Main chưa có ngày bắt đầu, ngày kết thúc và chưa được phân bổ vào các Version/Sprint 6 & 7. | **TRUNG BÌNH** | `PENDING_WRITE_APPROVAL` | Chủ dự án xem xét tài liệu [`MAIN_WRITE_APPROVAL_PREVIEW.md`](file:///d:/AI%20project/QLDAPM%20chat/docs/ai-multi-agent-upgrade/antigravity-continuation/MAIN_WRITE_APPROVAL_PREVIEW.md) và cấp quyền ghi. |
| **BLK-03** | **Live Gemini Supervisor UAT** | Bài kiểm thử kết nối API ngoài bị tạm dừng do kích hoạt Điều kiện Dừng Section 9, Rule E2 (tránh lãng phí quota khi Main chưa hỗ trợ đủ tác tử). | **TRUNG BÌNH** | `HALTED_FOR_SAFETY` | Tự động mở khóa ngay sau khi BLK-01 được giải quyết. |

---

## 2. KỸ THUẬT NỢ VÀ CÁC ĐIỂM CẦN CẢI TIẾN TRONG TƯƠNG LAI (TECHNICAL DEBT)

Dù candidate v2 đã vượt qua 100% các bài kiểm thử hợp đồng, đội ngũ kỹ thuật ghi nhận các điểm có thể tối ưu thêm trong các phiên bản tiếp theo:

1. **Bộ nhớ tạm thời (TTL Cache) của Second Brain:**
   - *Hiện trạng:* Các câu truy vấn kiến trúc tương tự nhau vẫn phải thực hiện quét toàn văn (FTS) hoặc tính vector trong SQLite.
   - *Đề xuất tương lai:* Bổ sung lớp Redis LRU cache ngắn hạn (5 phút) cho các truy vấn phổ biến của vai trò Dev.
2. **Kích thước Docker Image Candidate:**
   - *Hiện trạng:* Image `qldapm-ai:rd-qual-20261021-v2` có dung lượng khoảng ~1.2GB do chứa đầy đủ các thư viện kiểm thử và công cụ phân tích tĩnh.
   - *Đề xuất tương lai:* Sử dụng multi-stage build trong Dockerfile để loại bỏ các dev dependencies ở image phục vụ production, giảm kích thước xuống dưới 500MB.
3. **Cơ chế Retry thông minh khi Gemini API gặp Rate Limit:**
   - *Hiện trạng:* Hệ thống ngắt an toàn và trả về mã lỗi khi bị 429 Too Many Requests từ phía Google API.
   - *Đề xuất tương lai:* Áp dụng thuật toán Exponential Backoff kết hợp Jitter để tự động thử lại sau vài giây khi hạn mức Free Tier bị nghẽn tức thời.

---

## 3. CÁC QUYẾT ĐỊNH CHỜ Ý KIẾN CHỦ DỰ ÁN (PENDING DECISIONS)

Để tiếp tục đưa hệ thống vào trạng thái hoàn thiện toàn diện, kính đề nghị Chủ dự án xem xét và ra quyết định cho 3 hạng mục sau:

1. **Quyết định 1 (Về nâng cấp Gateway):** Phê duyệt thay thế image Gateway trên Main bằng `qldapm-ai:rd-qual-20261021-v2`.
2. **Quyết định 2 (Về ghi lịch trình 7 Sprint):** Phê duyệt chạy script cập nhật ngày và phiên bản cho 329 Work Packages trên Main theo file `FINAL_7_SPRINT_NATIVE_PROPOSAL.csv`.
3. **Quyết định 3 (Về kích hoạt Live UAT):** Phê duyệt bấm chạy 1 lượt Live Gemini Supervisor UAT sau khi hoàn tất nâng cấp Gateway.
