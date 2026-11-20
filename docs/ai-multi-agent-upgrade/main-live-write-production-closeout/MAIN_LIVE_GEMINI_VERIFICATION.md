# Main Live Gemini verification — BLOCKED_OWNER_ADDITIONAL_LIVE_APPROVAL

Không có `MAIN_CURRENT_IMAGE_GEMINI_LIVE_READ_PASS` tại thời điểm báo cáo. Provider kết nối thật, nhưng cả hai lượt đã thực hiện chưa có Final Answer được host xác minh. Không dùng mock/deterministic summary để tuyên bố Gemini Live PASS.

| Run / producer Gateway | HTTP / generations | Tokens | Kết quả |
|---|---:|---:|---|
| 41d33283-69dd-4c6a-8cf9-41e5498e28ac /89f7686e… |4/2|5193|Native #367/#50 đọc thật; incomplete/blocked output; worker failed_or_unknown |
| b566b115-92aa-4730-95b4-d671acf462bc /3f88fd15… |2/1|2613|Native preflight thật; Google schema response thành công; host exact-claim validation reject |
| Image cuối bcd7158e… |0/0|0|Citation/facts fix đã deploy/qualify, chưa gọi lại Google |

Tổng **6 HTTP /3generations /7806 tokens**: prompt5048, candidates713, thoughts2045. Không lưu nội dung suy nghĩ, chỉ token metadata. Tất cả6 HTTP200, provider model version cuối được ghi `gemini-3.5-flash-lite`. Không retry CREATE, không Native mutation, không vượt ngân sách Owner. Lượt thứ hai để sửa lỗi chức năng thật; cả hai thất bại được giữ nguyên.

Bằng chứng: live-initial-failure.json, live-followup-failure.json, live-intent.json, live-followup-intent.json, live-run.json, main-live-initial-failed.txt. Không sửa error thành success. Budget đã hết, không tự chạy lượt3.

## Image cuối và minimum retry

Gateway `sha256:bcd7158e4febfd276d47599bf3be514997fbd976a32fb71be0f12b7d80748168`; Core `sha256:a3214219127e61ff934d33b0c45031df8a315e6a5f44ff9754c7985e2adcbcbb`; sourceSHA `0cc3f4e59c18fffc31c088d399078b4047328ba5707cc6a6a2eb902442eb70f6`. Parity55Gateway/47Core, 118Windows/114Linux/21browser PASS offline trên current source. Read mode hiện chỉ đọc explicit Native IDs rồi một synthesis, schema citation IDs + parent/assignee facts đối chiếu Native, không model-executable tools. Không nới RBAC hay bỏ validation để ép PASS.

Cần phê duyệt riêng **thêm tối đa1 countTokens +1generateContent, một run READ-ONLY**, maxOutput3000, no retry, cùng key/model/project Free-only, dữ liệu #367/#50 đã lọc, không ghi/comment/delete. Preview chính xác: ADDITIONAL_LIVE_PREVIEW.md. Nếu được duyệt, tổng của cả phiên tối đa8HTTP/4generations; không tự vượt tiếp.

Billing: giữ cấu hình Free-only, proof/key/model nguyên hash; owner-attested, không kiểm tra Billing Console mới và không bật billing/paid fallback. Quota từ provider còn lại không được suy đoán.
