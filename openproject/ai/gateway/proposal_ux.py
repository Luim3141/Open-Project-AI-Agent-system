"""Proposal UX & Native Readback Verification Module (P08-06):
Provides Before/After diff calculation, Reviewer Agent summary synthesis,
and ensures receipts are NEVER marked as succeeded before verifiable native readback.
Supports 'PARTIAL_SUCCESS' receipts when mutations only partially apply.
"""
from .permissions import business_manager
from typing import Any, Literal

ReceiptStatus = Literal["PENDING_READBACK", "SUCCEEDED", "PARTIAL_SUCCESS", "FAILED_READBACK"]


def build_proposal_diff(
    current_item: dict[str, Any] | None,
    proposed_changes: dict[str, Any],
) -> list[dict[str, Any]]:
    """Builds clean, structured field-by-field diff between current native item and proposed mutation."""
    current_item = current_item or {}
    diffs = []

    # Map of field names to human-readable Vietnamese labels
    field_labels = {
        "subject": "Tiêu đề công việc",
        "description": "Mô tả / Yêu cầu",
        "status": "Trạng thái",
        "status_id": "Mã trạng thái",
        "assignee": "Người thực hiện",
        "assignee_id": "Mã người thực hiện",
        "startDate": "Ngày bắt đầu",
        "dueDate": "Ngày hoàn thành (Hạn chót)",
        "estimatedTime": "Ước tính thời gian (giờ)",
        "parent_id": "Công việc cha (Parent)",
        "comment": "Bình luận bổ sung",
    }

    all_keys = sorted(set(proposed_changes.keys()))
    for key in all_keys:
        proposed_val = proposed_changes[key]

        # Extract current value
        if key == "status":
            current_val = current_item.get("_links", {}).get("status", {}).get("title") or current_item.get("status")
        elif key == "assignee":
            current_val = current_item.get("_links", {}).get("assignee", {}).get("title") or current_item.get("assignee")
        else:
            current_val = current_item.get(key)

        is_changed = (str(current_val) != str(proposed_val))
        diffs.append({
            "field": key,
            "label": field_labels.get(key, key),
            "before_value": current_val if current_val is not None else "(Chưa thiết lập)",
            "after_value": proposed_val if proposed_val is not None else "(Xóa/Để trống)",
            "is_changed": is_changed,
        })

    return diffs


def synthesize_reviewer_summary(
    proposal: dict[str, Any],
    actor_role: str,
    lock_version_match: bool = True,
) -> dict[str, Any]:
    """Generates independent verification review for proposal before PM confirmation."""
    is_pm = (business_manager(actor_role))
    conflicts = []
    warnings = []

    if not is_pm:
        conflicts.append("RBAC_VIOLATION: Chỉ vai trò PM mới có quyền duyệt và thực thi thay đổi nghiệp vụ.")

    if not lock_version_match:
        conflicts.append("STALE_VERSION_CONFLICT: Phiên bản công việc đã thay đổi kể từ khi tạo đề xuất. Cần đối soát lại.")

    action = proposal.get("action", "")
    if action in {"create_work_package", "update_work_package", "transition"}:
        args = proposal.get("arguments", {})
        if not args.get("subject") and action == "create_work_package":
            conflicts.append("MISSING_REQUIRED_FIELD: Tiêu đề công việc không được để trống.")

    verdict = "REJECTED" if conflicts else "APPROVED_FOR_REVIEW"
    return {
        "reviewer": "ReviewerAgent",
        "verdict": verdict,
        "is_safe_to_execute": False,
        "conflicts": conflicts,
        "warnings": warnings,
        "evidence_verified": False,
        "summary": (
            "Reviewer Agent: Đề xuất hợp lệ, đúng phân quyền RBAC và không xung đột phiên bản."
            if not conflicts else
            f"Reviewer Agent cảnh báo: {'; '.join(conflicts)}"
        ),
    }


def verify_native_readback(
    native_packages: list[dict[str, Any]] | None,
    target_id: int,
    expected_changes: dict[str, Any],
) -> dict[str, Any]:
    """Verifies that mutations actually exist in the native OpenProject database.
    NEVER marks SUCCEEDED before verifiable readback.
    """
    if not native_packages:
        return {
            "status": "PENDING_READBACK",
            "verified": False,
            "message": "Chưa đọc lại được dữ liệu native từ OpenProject; giữ trạng thái chờ xác minh.",
            "matched_fields": [],
            "unmatched_fields": list(expected_changes.keys()),
        }

    # Find the target package
    target = None
    for pkg in native_packages:
        if pkg.get("id") == target_id:
            target = pkg
            break

    if not target:
        return {
            "status": "FAILED_READBACK",
            "verified": False,
            "message": f"Không tìm thấy công việc #{target_id} trong OpenProject sau thao tác.",
            "matched_fields": [],
            "unmatched_fields": list(expected_changes.keys()),
        }

    matched = []
    unmatched = []
    for field, expected_val in expected_changes.items():
        if field == "status":
            actual_val = target.get("_links", {}).get("status", {}).get("title")
        elif field == "assignee":
            actual_val = target.get("_links", {}).get("assignee", {}).get("title")
        else:
            actual_val = target.get(field)

        # Check match (lenient on string representation)
        if str(actual_val).casefold() == str(expected_val).casefold():
            matched.append(field)
        else:
            unmatched.append(field)

    if len(matched) == len(expected_changes):
        status: ReceiptStatus = "SUCCEEDED"
        msg = "Xác thực đọc lại native 100% khớp: mọi thay đổi đã được ghi nhận trên OpenProject."
    elif len(matched) > 0:
        status = "PARTIAL_SUCCESS"
        msg = f"Xác thực một phần (Partial Success): {len(matched)}/{len(expected_changes)} trường đã cập nhật; trường chưa khớp: {', '.join(unmatched)}."
    else:
        status = "FAILED_READBACK"
        msg = "Đọc lại native cho thấy thay đổi chưa được áp dụng trên OpenProject."

    return {
        "status": status,
        "verified": (status == "SUCCEEDED"),
        "message": msg,
        "matched_fields": matched,
        "unmatched_fields": unmatched,
    }
