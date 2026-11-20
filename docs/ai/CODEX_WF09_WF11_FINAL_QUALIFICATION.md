# WF09 / WF11 — qualification hiện hành

**PARTIAL, chưa có full business bug closure.** Hai quyết định thật QA23 và PM19 đã accepted/current đúng evidence `d4d5aa97-a716-550d-88e9-de04b9caf9c9`, hash `311a3b76ebda820a6383a393d393a86ed9bb041a5dfdbe9d5c8216ec4928a034`. Fresh six-role reads trong `CODEX_WF02_TRUSTED_DELETE_HUMAN_CHAIN_RESULT.json` xác nhận chain này còn hợp lệ; không review lại hoặc tiêu thụ thành Native approval.

Artifact bao gồm sáu Native field predicates trên #375v0. Nó là automated readback evidence, không phải chứng cứ sửa một lỗi ứng dụng. Source/version, signed producer/artifact, independent QA/Manager, reviewer revocation, exact hash, duplicate409, rollback audit và retest/source invalidation có unit/integration/actual Native clone evidence. Các test thuộc bộ518Windows/503Linux+15skips/15Ruby; không coi tổng test là số business workflows.

Core `QaEvidenceReceipt` và Native mutation transaction hỗ trợ packet automated v1 cho các cặp QA transition cụ thể; exact human proposal/hash còn bắt buộc. `get_gate/change_gate` Native-mode422 vẫn giữ. #371 hiện NEW, nên không thể nhảy vào REVIEW. Policy yêu cầu story/AC/scope, analysis, development child, checklist, actual implementation/build/test-case proof và reviewer. Retest làm mất BA/PM approvals cũ; không được giữ chúng để lách release gate.

Các khoảng trống cần hoàn thiện: Native-compatible source/analysis/fix phase preparation; chứng cứ fix/build thực; retest cùng acceptance criteria; BA/PM fresh release review; closure của children, deployment và smoke evidence. Manual Native attestation hiện cần own QA comment/attachment; Native QA attachment upload permission không có, và Core packet hiện chỉ nhận automated readback kind. Không dùng PM token để upload thay QA hoặc nhận một chuỗi “Fixed” làm bằng chứng.

Các report fixture cũ về full mocked bug→fix→retest chain chỉ chứng minh fixture policy; không phải actual Main/full Native business closure. Tham chiếu `CODEX_WF11_QA_REVIEW_NATIVE_CLONE_RESULT.json`, `CODEX_QA_REVIEW_FRESHNESS_FINAL_READBACK.json`, `CODEX_WF11_CURRENT_NATIVE_READINESS.json`, `CODEX_FINAL_QA_APPROVAL_REQUIREMENTS.md`. Không có Main transition mới trong giai đoạn này.
