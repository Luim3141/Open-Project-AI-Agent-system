# Native relations và derived scheduling — contract triển khai Main

26/10: Core/Gateway versioned scope/exact proposal/receipt bridge đã deploy Main89777ef1/4495d944, riêng WF10 version7951e328. Core và Gateway clone đã PASS Native scheduling, role, replay, concurrency, one-POST recovery và PostgreSQL rollback; Main24readonly/policy checks PASS, không có Main Native write mới. Các đoạn “chưa triển khai” bên dưới mô tả baseline trước candidate. Xem `CODEX_NATIVE_DEPENDENCY_CORE_CLONE_RESULT.json` và phần Native dependency trong `architecture.md`.

Native baseline mới đã qualify9WP/4relation trong clone: relation giữa Task cha có manual leaves không đổi lịch; relation giữa Subtasks làm đổi384→parent382→Epic380. Hai expectation thất bại trước đó được giữ rõ trong artifact, không sửa thành business PASS.375WP/352relation cũ của clone không đổi. Scope preview phải nêu khả năng đổi lịch của descendants/ancestors, không hứa ngày dự đoán. Không có relation write Main hoặc approval mới.

Phạm vi: Main project5. **SOURCE DESIGN / NOT_IMPLEMENTED**, chưa có relation write hoặc approval mới. Giữ nguyên352relations lịch sử và các hierarchy đã nghiệm thu. Đây là bước kế tiếp sau Supervisor QA handoff; không coi nó là workflow PASS.

Đã kiểm tra source thực trong Core Web `sha256:edc9f2b23db00a25fa73acbbd3dafb1f609b17d37ea0790fde9db9778b37e8fa`:

- `work_package_relations_api.rb` tạo qua `Relations::CreateService`; `notify=false` tắt notification trong service context.
- `Relations::BaseContract` yêu cầu cả hai endpoint visible và có `manage_work_package_relations`, dùng Native relatability/cycle validation. Không tự thay bằng graph validator riêng.
- `Relations::BaseService` gọi rescheduling cho `follows`. `Rescheduling` lưu các dependent Work Packages; vì vậy không thể giả định chỉ một relation row thay đổi.
- Trong `Relation`, `predecessor=to`, `successor=from`. `follows` có thể đổi successor sang automatic scheduling khi đó là dependency đầu tiên và successor không có child.

Vendor mô tả type/reverseType và lag; quyền Native vẫn là điều kiện bắt buộc. [OpenProject Relations API](https://www.openproject.org/docs/api/endpoints/relations/). Source của image hiện hành là bằng chứng quyết định cho implementation, không suy đoán từ một phiên bản API khác.

Thiết kế tối thiểu đề xuất, chưa được triển khai:

1. Qualify trước trên clone: hai test Tasks, relation `follows`, lag0/positive, direction, duplicate/cycle denial, hai version, automatic schedule, parent/ancestor propagation và failure rollback. Dùng identities thật trong clone nhưng mọi quyết định là fixture, không phải approval Main.
2. Reuse proposal/hash/approval và Core MutationReceipt hiện có. Contract mới phải ràng buộc actor xác thực, exact proposal ID/hash, cả hai Native IDs/lockVersions, type/lag và scope ảnh hưởng được duyệt. Không nhận `approved`, `admin`, `role` hoặc actor từ caller làm quyền.
3. Core lấy project lock trước khi đọc/khóa các rows theo thứ tự ổn định, xác minh fresh Native permission cả hai endpoint và Native contract; cùng transaction cho relation, derived changes và receipt. Không gọi `Relation.create!` để bỏ qua `Relations::CreateService`.
4. Derived scope phải được preview và chứng minh. Nếu chưa biết các Work Packages có thể bị reschedule, giữ PARTIAL và chưa cho Main execution; không biến approved two-WP request thành quyền sửa các WP khác.
5. Lost reply chỉ reconcile exact persisted receipt, không POST lại. Readback xác minh relation endpoints/type/lag và tất cả version/date changes. RAG sync phải theo exact affected sources, không chỉ hai endpoint.
6. WBS giữ contract tree completion cũ; dependency execution cần progress riêng có provenance. `depends_on` hiện là sequencing của draft, không tự suy ra đã có Native relation hoặc tự tạo quan hệ parent/child trái Native policy.

Baseline Native qualification đã chạy trên clone, chưa phải implementation bridge: Owner18 tạo follows/lag0 làm successor377 chuyển26–27/10→28–29/10; PM19 tạo lag2 làm successor379 chuyển26–27/10→30/10–02/11. Hai successor đổi manual→automatic và lockVersion0→1. Bốn role còn lại bị chặn; duplicate và cycle bị từ chối. Tất cả375WP cũ và352relation rows cũ trong clone giữ nguyên. Main không có write. Xem `CODEX_NATIVE_RELATION_BASELINE_CLONE_RESULT.json`.

Các giới hạn thật: chưa qualify parent/ancestor/broader graph impact, chưa có versioned Gateway proposal/hash/receipt bridge và chưa có exact Main proposal/approval cho relation. Không đổi source type/status/schema, credentials, model/quota, Staging hoặc dữ liệu nghiệp vụ để hoàn thành nghiên cứu.
