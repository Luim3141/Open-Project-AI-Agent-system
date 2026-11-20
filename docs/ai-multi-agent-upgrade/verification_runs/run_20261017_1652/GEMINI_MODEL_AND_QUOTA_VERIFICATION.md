# XÁC MINH MODEL VÀ QUOTA GEMINI API (GEMINI_MODEL_AND_QUOTA_VERIFICATION.md)

**Audit Run:** `run_20261017_1652`  
**Thời gian xác minh:** 2026-10-17T16:55:00+07:00  
**Chứng cứ xác thực:** Ảnh chụp màn hình Google AI Studio Rate Limits từ Chủ dự án (`media_1792230531912_0284e9e2.png`).

---

## 1. THÔNG SỐ MODEL VÀ QUOTA XÁC MINH CHÍNH THỨC

Từ bằng chứng trực quan trên giao diện Google AI Studio của dự án:

| Thông số | Giá trị xác nhận từ AI Studio | Cấu hình Gateway (`MODEL_ALLOWLIST.json`) | Trạng thái khớp |
|---|---|---|---|
| **Tên Model** | **`Gemini 3.5 Flash Lite`** | `"gemini-3.5-flash-lite"` | **100% Khớp** |
| **Phân loại** | Text-out models | Text-out models | Khớp |
| **Hạn mức RPM** | **15 requests/minute** | `"rpm": 15` | Khớp |
| **Hạn mức TPM** | **250.000 tokens/minute** | `"tpm": 250000` | Khớp |
| **Hạn mức RPD** | **500 requests/day** | `"rpd": 500` | Khớp |

### Mức sử dụng tại thời điểm ghi nhận (Snapshot):
- **RPM:** `6 / 15` (40.0% hạn mức phút)
- **TPM:** `39.4K / 250K` (15.7% hạn mức token phút)
- **RPD:** `214 / 500` (42.8% hạn mức ngày)

> [!IMPORTANT]
> Các con số trên là **snapshot tức thời**, không phải hạn mức cố định vĩnh viễn. Quota Controller của hệ thống phải hoạt động với biên an toàn (safety buffer) và không được giả định quota luôn ở mức tối đa.

---

## 2. HIỆU CHỈNH KẾT LUẬN DEF-03

- **Đánh giá trước đó:** Đợt Wave 0 đặt nghi vấn về tên model `gemini-3.5-flash-lite` do chưa đối chiếu trực tiếp với console AI Studio của dự án.
- **Hiệu chỉnh chính thức:** Nhận định nghi vấn trên là **SAI**. Model `gemini-3.5-flash-lite` là model chính thức, đang hoạt động thực tế trên Google AI Studio của Chủ dự án, đã trả về `HTTP 200 OK` khi chạy live regression tests.
- **Trạng thái DEF-03:** Chuyển từ `OPEN` sang **`RESOLVED / VALIDATED BY OWNER SCREENSHOT & OFFICIAL AI STUDIO`**.
- **Chỉ thị:** Giữ nguyên 100% model `gemini-3.5-flash-lite`, tuyệt đối không đổi sang `gemini-1.5-flash`.

---

## 3. CHÍNH SÁCH BẢO VỆ QUOTA & KHÔNG PHÁT SINH PHÍ

1. **Chế độ kiểm thử an toàn:**
   - Ưu tiên sử dụng mock / deterministic read cho các bài test hồi quy nội bộ.
   - Không chạy stress test hoặc cố tình tiêu thụ cạn kiệt 286 lượt RPD còn lại chỉ để kiểm tra.
   - Không sử dụng nhiều API keys hay đổi project ID để né quota.
2. **Cơ chế Circuit Breaker:**
   - Hệ thống tự động kích hoạt `WAITING_QUOTA` khi chạm 80% ngưỡng RPD hoặc khi nhận mã HTTP 429 từ Google.
   - Tự động làm mới quota theo chu kỳ ngày tại `00:00 PST` (Pacific Standard Time) theo đúng đặc tả của Google AI Studio.
3. **Trạng thái Billing Verification:**
   - Cấu hình ứng dụng: Khóa cứng `paid_api_disabled: true`, `auto_enable_billing: false`, `provider_policy: "FREE_ONLY"`.
   - Google Cloud Console Billing Gate: Ảnh Rate Limits chỉ xác nhận hạn mức sử dụng gói Free, chưa hiển thị trang quản lý phương thức thanh toán của GCP. Do đó, theo nguyên tắc kiểm toán độc lập nghiêm ngặt, cổng này được ghi nhận:
   - **Trạng thái:** **`BLOCKED_OWNER_VERIFICATION`** (Tiếp tục thực thi mọi tác vụ kiểm thử và vận hành không làm phát sinh chi phí).
