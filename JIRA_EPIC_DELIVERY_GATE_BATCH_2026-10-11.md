# QAG3 — Epic scope / delivery gates

## Apply đã VERIFIED sau phê duyệt

Owner trả lời **Duyệt lưu lô Epic inactive** cho đúng preview/hash bên dưới; registered qag3-admin apply_change trả VERIFIED. Independent inspect_workflow đọc **Epicv7/4f007f20-c611-4a35-aa8c-1c5083b6a2d7**; có đúng screen10011/readiness tại2 và screen10011/acceptance tại6. Assertions bỏ riêng additions mới đối chiếu before PASS: giữ6statuses/10transitions, mọi oldrule/PM/childDone/reason/Resolution, routing/graph/layout/metadata. Sau ghi inspect_scheme vẫn10003; inspect_automation readComplete=true chỉA01 DISABLED. Không Task/Subtask write/migration/automationenable/monitorresume. Các dòng preview-chờ duyệt dưới là lịch sử trước apply, không current state.

## Kết quả hiện hành

Official session atlassianUserInfo/getAccessibleAtlassianResources/getJiraIssue(QAG3-1) xác minh owner712020:0d04982c-00bf-46af-b3a7-446d0f44edfb, site luimjiraqldapm.atlassian.net, cloud560ef0cc-d24b-4613-98d3-d541afe8f32b, QAG3. Discover không trả workflow-validator admin write; dùng supplementary qag3-admin đã duyệt, không browser/REST trực tiếp.

Owner duyệt deploy manifest SHA256 **ba890f52fc7aca64b73d4a360571935c759986d7b52f952525e3429723af715e**. Hash kiểm tra trước deploy; Forge development **2.4.0** Success2026-10-10T21:35:48.550Z (11/10/2026 +07), lint No issues found. Independent Jira catalog đủ10validators. Tám modules/runtime/app cũ đối chiếu bytehash5c99687f… PASS. Không scopes/function/storage/egress/dependency/billing mới hoặc register/install lại.

Preview **317db13d-b076-4cf8-a30f-db89bd8d8ef8**, SHA256 **b19116fa1fc7ad487597ec17940f4fb97b5e374296783bc4f05c7cd9e89dd3cb**, validation errors=[]/blockers=[]. **Chưa apply** tại thời điểm ghi tài liệu này; chờ human exacthash approval, hết hạn900s. Epic trước ghi v6/e9bfab73-dc0c-46b1-9304-f5520e12f9a7. Lô chỉ thêm screen10011/readiness vào Approve scope2 và screen10011/acceptance vào Accept Epic6; giữ graph/Resolution/PM/childDone/reason/layout. Không migration hoặc bật automation.

## Gate READY

PM thật trong hai account đã chốt; Epic QAG3 nguồn NEW; active owner; description không trắng. Evidence mới ngay trên transition, mỗi dòng duy nhất và không trắng:

```text
Scope version: <phiên bản phạm vi>
Scope tasks: <danh sách key Task thực, phân cách dấu phẩy>
Acceptance criteria: <AC hoặc tham chiếu tài liệu>
Scope result: APPROVED
Evidence: <bằng chứng duyệt phạm vi>
```

Ít nhất một Task con QAG3, đúng type10011; danh sách khai báo phải chứa chính xác mỗi key con một lần, không thiếu/thừa/trùng. Đây là PM phê duyệt phạm vi hiện tại, không khóa Parent hoặc tạo snapshot Sprint độc lập. AC/evidence text không chứng minh nội dung tài liệu đã được kiểm tra.

## Gate DONE

PM thật, nguồn REVIEW; active owner; summary/description/assignee không thay đồng thời với nghiệm thu. Evidence mới, mỗi dòng duy nhất:

```text
Scope version: <phiên bản phạm vi>
Scope tasks: <danh sách key Task thực, phân cách dấu phẩy>
Integration result: PASS
Handover result: COMPLETE
Evidence: <bằng chứng tích hợp và bàn giao>
Retest: PASSED hoặc NOT REQUIRED
Bug references / retest rationale: <tham chiếu và kết quả hoặc lý do>
```

Checklist dùng options hiện có10020AC/10022QA/10025BA/10026PM/10027Testsmoke; đúng một10023Retestpassed hoặc10024Retestnotrequired và khớp evidence. Không thêm option/field mới. Lead review vẫn thuộc Task gate còn phải hoàn thiện; checkbox QA/BA ở Epic không phải chữ ký riêng của QA/BA.

Phạm vi chính xác/nonempty; mọi Task Done10009 và mọi Subtask hiện thời của chúng Done10009; thiếu/null/loại con khác/dữ liệu không đọc được đều fail-closed. Predicate này không kiểm chứng QA provenance từng descendant hoặc nguyên tử giữa nhiều issue. Retest/evidence là xác nhận nghiệp vụ của PM, chưa hardgate Fix Bug/linked defect.

## Validation / rollback / còn thiếu

Node fixtures PASS positive/negative: sai PM/inactive owner/source, scope thiếu/thừa/trùng/type/project, evidence rỗng/cũ/duplicate, missing checklist/retest conflict, Task hoặc Subtask chưaDone, pending edits.91Python tests PASS gồm builder additive/idempotent/catalog missing/screen conflict/mapping conflict và registered stdio17tools. Jira APIvalidation/catalog/lint không thay Jira expression engine/E2E hoặc cost hardcap.

Audit/before tại `%LOCALAPPDATA%\QLDAPM\jira-admin-audit\317db13d-b076-4cf8-a30f-db89bd8d8ef8.*`. Sau apply cần đọc độc lập và preservation assertions. Rollback workflow dùng before/currentversion/freshpreview/approval; deploy rollback giữ source8modules qua approval riêng. Không uninstall app đang được workflow tham chiếu hoặc replay timeout.

Còn Task Lead/BA identity, Fix Bug retest, scope snapshots/Parent edits và concurrency, quyền/actor automation, Jira E2E, migration329mục và A01–A05. Bot giữPAUSED, không HR scores/KAN/SAM1/OpenProject changes.

Nguồn primary đã đối chiếu: [Forge workflow validator](https://developer.atlassian.com/platform/forge/manifest-reference/modules/jira-workflow-validator/) và [Jira expression types](https://developer.atlassian.com/cloud/jira/platform/jira-expressions-type-reference/). Input trên transition screen là dữ liệu chờ ghi; expression không trả true hoặc lỗi thì validator từ chối. Không suy đây là multi-issue lock.
