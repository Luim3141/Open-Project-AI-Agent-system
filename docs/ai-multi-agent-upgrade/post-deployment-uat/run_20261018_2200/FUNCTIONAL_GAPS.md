# Phạm vi chưa nghiệm thu

| ID | Trạng thái | Giới hạn thực tế | Việc còn cần |
|---|---|---|---|
| G2-LIVE-GEMINI | BLOCKED | Free-only policy/key lưu bền đã giữ; live billing/quota hiện tại chưa được owner xác minh theo gate mới.58mock tests không chứng minh Google thật | Owner xác minh Free/No billing account/quota đúng project+model; duyệt1minimal smoke trước mọi inference |
| DRAFT-CONVERSION | BLOCKED feature | Supervisor trả report/draft/plan; không tự chuyển thành executable canonical proposal. PM dùng tool form tạo preview rồi approve/reject;9UI/API assertions chứng minh đường này | Nếu cần một nút “tạo preview từ draft”, phải thiết kế mapping/validation và test hash/ACL/lockVersion/PM consent; không tự bật auto-approval |
| GEMINI-NL-FULL-CHAIN | BLOCKED | Chưa có bằng chứng live Gemini → tools → proposal → UI trên build này | Sau G2, dùng fixture cô lập và budget/one-call approval cụ thể. Minimal smoke không tự nghiệm thu workflow ghi |
| SPRINT-LIFECYCLE | BLOCKED ngoài phần đọc |5role đọc5Sprint thật PASS; permission query chỉ PM có lifecycle quyền. Không start/finish/reassign dữ liệu Sprint đang phục vụ | Dùng owned Sprint fixture trên clone; không coi quyền true là bằng chứng mutation thành công |
| PHYSICAL-CLIENT | BLOCKED môi trường |5account/context thật qua public tunnel trên1host, chưa5physical clients | User thực hiện handoff/human UAT ở client riêng khi thuận tiện; không cần Radmin |
| N8N-ROLE-SCOPE | PASS theo thiết kế |5role dùng Daily Brief trong Core; execution editor/history là quyền operator riêng, loopback | Không chia sẻ owner credentials cho nhân viên; lịch thật có history, UAT mới chỉ trigger trên clone |
| CAPACITY-20 | DEFERRED_BY_OWNER | Không nằm trong release local5users | Không chạy hoặc quảng cáo20user capacity |

Second Brain hiện là SQLite FTS5/Native citations+fresh ACL, không phải pgvector/semantic embedding. Không coi provenance là con người đã nghiệm thu tính đúng nội dung AI. Main chưa được promote.
