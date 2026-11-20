# Main continuation — kiểm chứng độc lập, 21/10/2026 14:36+07

Phiên này giữ Staging, đọc Main và chạy qualification offline. Không deploy, ghi Main, gọi Google mới hoặc replay live runs. Giữ báo cáo/log cũ.

- Main Core95da6c8e/Gatewaya84bc31a đang phục vụ. Native PM19/Project5 identity và đọc329WP PASS.
- Tiến trình khác ghi329ngày,318Version assignments và thêm3Versions trong cửa sổ audit. Audit này không thực hiện các ghi đó. Stage372WP/352relations/4Versions đồng thời giữ nguyên fingerprints.
- So với CSVv2 SHA256 e25fa52a1f9999f971d4d0ecc26b1e0a1e84334e7674f2e9865583ca29f7301b:329rows, dates/assignee/status/schedulingflags/Sprint/Version khớp; parent rollup không sai lệch; boundaries ngày làm việc;7Sprints05/10/2026–08/01/2027 ở in_planning. Chưa requalify343dependencies/capacity. Xem main-schedule-readback.json.
- **70/70offline tests PASS** trong30.981s. Lần đầu có62passing+2importerrors do module search path; giữloggốc, sửa invocation và rerun toàn bộ70PASS. Model responses trong tests là synthetic.
- Main live runca0c3b3f… có BA+QAplan/provider receipts thật nhưng failed_or_unknown/GEMINI_REVIEW_FAILED. Reviewer từ chối#102 ngoài Native context#49. Runc92242b2… cũng failed vì nhắc#49 từcontext#38. Safety refusal đúng không phải phân tích end-to-end thành công. Không retry hoặc nới guard.
- Mainknowledge.sqlite có0documents. Tài liệu mới gán Birdsong/pgvector cho QLDAPM là NOT VERIFIED. Runtime QLDAPM thực là SQLite/FTS cộng Native actor/project/version checks.
- n8n containers/workflows hiện xác minh thuộc Stage. Mainautomation_runs/daily_briefs0 tại baseline. Không repointworkflowStage/reusemachinekey để lấp nghiệm thuMain.
- Policy cấu hình RPD500, guard90%=450, không phải1500 như một handoff mới. Googleproject quota chia sẻ giữa Main/Stage; chưa xác minh billing trực tiếp.

Chưa ký nghiệm thu Main100%. Tiếp tục source/fixture work trong phạm vi đã duyệt; giữ Stageimages/state/URL/mountsources/n8nlinks. Đọc STAGING_DEMO_READINESS.md vàpreservation.json trước bướcMain tiếp theo. ResetPM7Stage là phê duyệt riêng, không cho phép đổi authMain.
