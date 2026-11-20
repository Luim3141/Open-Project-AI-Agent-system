# WF10 Native dependency writes — design preview, chưa triển khai

Actual Main OpenProject17.9.1 exposes Owner18/PM19 `POST /api/v3/work_packages/{id}/relations`; BA20/QA23 không có addRelation link. Schema/form discovery routes được kiểm tra trả404. Không kết luận toàn API không hỗ trợ: create link tồn tại và local source xác nhận Relations::CreateService/CreateContract.

Native payload có type/lag/description/from/to, không có endpoint lockVersion. Contract kiểm tra visibility, manage_work_package_relations ở cả hai endpoint, circular dependency và type. `follows` có thể chuyển successor sang automatic scheduling và cập nhật dependent packages. Source: `/app/app/services/relations/base_service.rb`, `relations/concerns/rescheduling.rb`, `app/contracts/relations/base_contract.rb`, `lib/api/v3/work_packages/work_package_relations_api.rb` trong serving Main Core. Official reference: [OpenProject relations](https://www.openproject.org/docs/api/endpoints/relations/); serving17.9.1/source là căn cứ khi khác docs mới.

Không biến `depends_on` của existing WBS thành Native relations tự động: hiện đó là sequencing constraints, có thể bao gồm ancestor và không nhất thiết là một valid follows edge. Canonical RAG document hiện chưa chứa relation edges; gọi refresh không chứng minh edge đã được index.

Thiết kế cần qualification trước: authenticated own actor, exact approved endpoints/type/lag và expected endpoint/affected-closure versions; Native contract trong transaction có row locks/version precondition, idempotency event/receipt, `notify=false`, affected scheduling closure readback, explicit unknown-outcome hold/no POST replay và RAG edge semantics. Nếu cần Core extension/migration, phải có preview riêng và isolated tests; không giả fresh GET thành atomic locking.

Status: **BLOCKED_VERSIONED_RELATION_AND_DERIVED_SCHEDULE_CONTRACT**. Không relation POST/PATCH/DELETE nào được thực hiện trong phiên này. Existing relation reads, old352 relation rows và WBS tree được giữ.
