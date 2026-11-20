# SPRINT REVIEW TEMPLATE — riêng tư, chưa có đánh giá

Đây là biểu mẫu trống được phép tạo/upload theo yêu cầu bootstrap; **không chứa điểm hay đánh giá thành viên thật**.
Authority: AGENTS.md §5. Không dùng làm cơ sở duy nhất cho HR, kỷ luật, lương/thưởng hoặc xếp hạng.

## 1. Metadata và phạm vi

- Project / cloudId / board / Sprint ID & name: <đọc Jira>
- Planned start/end; actual start/end; timezone: <evidence hoặc MISSING>
- Snapshot timestamp; người lập; review version: <...>
- Nguồn: <issue keys, changelog pages, QA/review notes, PR/test evidence>
- Publication: PRIVATE; PM review: PENDING.
- Approval lưu/chia sẻ assessment: NOT REQUESTED/APPROVED, người duyệt/thời điểm/phạm vi: <...>
- Loại dữ liệu: REAL / SIMULATION (không trộn). Sprint tương lai/chưa có việc không được chấm.
- Vai trò/người tham gia: <accountId xác minh>; capacity được người dùng cung cấp và nguồn: <...>
- Coverage quyền đọc/phân trang, thiếu evidence hoặc sai dữ liệu cần sửa: <...>

## 2. Baseline, scope changes và chỉ số nhóm

| Chỉ số | Baseline / kết quả | Nguồn & định nghĩa / giới hạn |
| --- | --- | --- |
| Sprint goal | <...> | <goal và acceptance evidence> |
| Scope cam kết đầu Sprint | <issue ID, estimate, assignee> | <snapshot bất biến + timestamp> |
| Scope thêm/bớt | <...> | <scope change ID/người duyệt/lý do> |
| Scope đã nghiệm thu | <...> | <AC/test/review, không chỉ status> |
| Carryover/spillover | <...> | <scope baseline chưa được nghiệm thu> |
| Throughput/WIP | <...> | <không cộng hai lần Task/Subtask> |
| Lead/cycle time | <...> | <mốc bắt đầu/kết thúc; lịch, dữ liệu đủ> |
| Defect/escaped/reopen | <...> | <liên kết và attribution có căn cứ> |
| Blocked time / dependencies | <...> | <lý do và evidence thời gian, không đoán> |
| Scope change ratio | <...> | <định nghĩa denominator không đổi; rỗng → N/A> |

Chỉ số nhóm phục vụ cải tiến và forecasting, không phạt cá nhân. Point không phải giờ; velocity không phải năng lực cá nhân. Chỉ số không đủ dữ liệu ghi MISSING/N/A, không biến thành 0.

## 3. Phiếu mỗi người — lặp cho PM, BA, FE, BE, QA

- Người / accountId / vai trò: <...>
- Phần việc cam kết và phần việc nghiệm thu: <issue IDs + scope snapshot>
- Đóng góp chia sẻ/công việc khẩn/phần việc ít ticket: <evidence>
- Complexity, dependency, requirement changes, việc gián đoạn và capacity thực: <nguồn>
- Bối cảnh giới hạn: chỉ thông tin liên quan công việc được phép; không thu protected traits/PM/private message/surveillance.
- Self-review / correction / PM feedback: <pending hoặc evidence được phép>
- Không suy năng lực hoặc thái độ từ ticket count, point, worklog thiếu, hay bug chưa rõ nguyên nhân.

| Dimension | Weight | Evidence gắn issue/nguồn và timestamp | Context / confidence / gaps | Provisional 0–5 hoặc INSUFFICIENT EVIDENCE |
| --- | --- | --- | --- | --- |
| Delivery reliability | 25% | <scope nghiệm thu được điều chỉnh hợp lý> | <...> | <...> |
| Quality | 25% | <review/test/reopen có attribution thận trọng> | <...> | <...> |
| Collaboration | 20% | <handoff/review/hỗ trợ/escalation> | <...> | <...> |
| Ownership & communication | 15% | <risk signaling/follow-through> | <...> | <...> |
| Technical/business contribution | 15% | <đầu ra và tác động theo vai trò> | <...> | <...> |

Chấm từng dimension chỉ khi đủ evidence; không lấy thiếu dữ liệu làm 0.
Overall mặc định **INSUFFICIENT EVIDENCE**. Chỉ tính nếu cả 5 dimension đều đủ bằng chứng:
`overall_0_to_5 = 0.25*delivery + 0.25*quality + 0.20*collaboration + 0.15*ownership + 0.15*contribution`.
Không đổi sang % “hiệu suất” hoặc so sánh chéo vai trò chưa calibration. Điểm chỉ provisional, PM/human review quyết định cuối.

## 4. Coaching và cải tiến

- Điểm tích cực có evidence: <...>
- Cơ hội cải tiến, phân biệt vấn đề hệ thống và trách nhiệm đã xác minh: <...>
- Action, owner, ngày kiểm tra và success criteria được thống nhất: <...>
- Rủi ro và support needed: <...>
- Ý kiến phản hồi/sửa factual errors của người được review: <...>
- PM decision: PENDING/APPROVED; không có auto HR action.

## 5. Quy trình tạo review thật

1. Xác minh project/Sprint/tài khoản; đọc Jira bằng MCP; đủ pagination và quyền.
2. Chụp evidence snapshot read-only, không fake changelog/worklog.
3. Tách thay đổi phạm vi khỏi delivery cá nhân, không ghi đè Sprint cũ; review evidence theo vai trò.
4. Draft trình riêng chủ dự án; thiếu một dimension → không overall.
5. Xin phép trước **lưu assessment thực**, comment/upload/publish/send hoặc cross-person comparison. Tạo template trống không thay approval đánh giá thật.
6. Cho người được review kiểm tra factual errors; PM xác nhận. Mỗi sửa tạo revision có lý do, giữ evidence bản gốc.
7. Không tự chạy nền, đóng Sprint, đổi Done hay gửi email chỉ để hoàn thiện review.

## 6. Biên bản điều chỉnh và access

| Version | Timestamp / editor | Thay đổi / lý do / nguồn | Ý kiến người được review | PM approval |
| --- | --- | --- | --- | --- |
| <...> | <...> | <...> | <...> | <...> |

Storage/access: <địa điểm và người được phép đã duyệt>. Không mặc định publish Jira/Artifacts/shared Drive hay bảng xếp hạng.
