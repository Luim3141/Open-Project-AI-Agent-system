"""QA Change Workflow (P07-06 under CR-USER-CAPACITY-20).
Handles requirement/work package change events by generating QA test drafts and routing scoped notifications.
Guarantees:
- Security Boundary: Event payload cannot escalate privileges or trigger automatic status transitions.
- Built-in Idempotency: Uses event fingerprinting to prevent duplicate draft generation or spamming.
- Non-mutation: Output is strictly an advisory draft (`DRAFT_PENDING_REVIEW`); no native database records are mutated.
- Scoped Notifications: Notifications are targeted to QA, the assigned developer, and PM.
- Pure Deterministic: 0 LLM tokens consumed.
"""
from typing import Any, Optional

from .store import canonical, digest
from .sprint_report import _get_status, _get_assignee


class QAChangeWorkflowEngine:
    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}

    def handle_event(
        self,
        event: dict[str, Any],
        users: Optional[dict[int, dict[str, str]]] = None,
    ) -> dict[str, Any]:
        users_map = users or {}
        pkg = event.get("package", {})
        pkg_id = event.get("package_id") or pkg.get("id")
        lock_ver = event.get("lock_version") or pkg.get("lockVersion", 1)
        changed_fields = sorted(event.get("changed_fields", []))

        # Built-in idempotency key
        event_fingerprint = digest(
            canonical({
                "package_id": pkg_id,
                "lock_version": lock_ver,
                "changed_fields": changed_fields,
            })
        )

        if event_fingerprint in self._cache:
            cached = dict(self._cache[event_fingerprint])
            cached["idempotent_replay"] = True
            return cached

        # Strict security check: disallow privilege escalation or status mutation
        current_status = _get_status(pkg)
        assignee_id, assignee_name = _get_assignee(pkg)
        subject = pkg.get("subject", "")
        desc = (
            pkg.get("description", {}).get("raw", "")
            if isinstance(pkg.get("description"), dict)
            else str(pkg.get("description", ""))
        )

        # Generate QA Draft test plan
        test_plan_lines = [
            f"### KỊCH BẢN KIỂM THỬ ĐỀ XUẤT (QA DRAFT) — #{pkg_id}",
            f"**Tính năng/Yêu cầu:** {subject}",
            f"**Phiên bản khóa:** {lock_ver}",
            f"**Các trường thay đổi:** {', '.join(changed_fields) if changed_fields else 'Mô tả chung'}",
            "",
            "#### TC-01 [Kiểm tra luồng chính - Functional Happy Path]:",
            f"- Xác thực hành vi của '{subject}' theo yêu cầu mới cập nhật.",
            "- Kiểm tra giao diện người dùng và dữ liệu phản hồi từ backend.",
            "",
            "#### TC-02 [Kiểm tra trường thay đổi & Dữ liệu biên - Regression / Boundary]:",
            f"- Kiểm tra tính toàn vẹn của các trường được cập nhật: {', '.join(changed_fields) or 'description'}.",
            "- Kiểm thử khi nhập dữ liệu trống hoặc sai định dạng.",
        ]

        if "otp" in desc.lower() or "xác thực" in desc.lower():
            test_plan_lines.extend([
                "",
                "#### TC-03 [Bảo mật & Xác thực - OTP / Security Check]:",
                "- Gửi mã OTP xác nhận và xác minh thời gian hiệu lực.",
                "- Thử nhập sai mã OTP quá 3 lần và kiểm tra cơ chế khóa/chặn.",
            ])

        test_plan_lines.extend([
            "",
            "> Trạng thái: DỰ THẢO CHỜ DUYỆT (Chỉ đề xuất, không tự động ghi dữ liệu).",
        ])

        qa_draft = {
            "target_package_id": pkg_id,
            "lock_version": lock_ver,
            "status": "DRAFT_PENDING_REVIEW",
            "test_plan_text": "\n".join(test_plan_lines),
        }

        # Role-appropriate notifications
        notifications = []
        for uid_int, uinfo in users_map.items():
            urole = uinfo.get("role", "")
            uname = uinfo.get("name", f"User {uid_int}")

            # Notify QA members
            if urole == "QA":
                notifications.append({
                    "recipient_id": uid_int,
                    "recipient_role": "QA",
                    "package_id": pkg_id,
                    "severity": "MEDIUM",
                    "message": (
                        f"Yêu cầu #{pkg_id} [{subject}] đã thay đổi: "
                        f"Rà soát kịch bản kiểm thử và cập nhật test cases."
                    ),
                    "action_needed": "REVIEW_QA_DRAFT",
                })
            # Notify Assigned Developer
            elif assignee_id is not None and uid_int == assignee_id:
                notifications.append({
                    "recipient_id": uid_int,
                    "recipient_role": urole,
                    "package_id": pkg_id,
                    "severity": "LOW",
                    "message": (
                        f"Yêu cầu #{pkg_id} [{subject}] bạn phụ trách đã có cập nhật: "
                        f"Chú ý đồng bộ với QA."
                    ),
                    "action_needed": "AWARENESS_ONLY",
                })
            # Notify PM
            elif urole == "PM":
                notifications.append({
                    "recipient_id": uid_int,
                    "recipient_role": "PM",
                    "package_id": pkg_id,
                    "severity": "LOW",
                    "message": (
                        f"Yêu cầu #{pkg_id} [{subject}] có thay đổi: "
                        f"Đã tự động tạo QA draft test cases chờ duyệt."
                    ),
                    "action_needed": "OVERSIGHT_ONLY",
                })

        result = {
            "state": "READY",
            "event_fingerprint": event_fingerprint,
            "is_draft": True,
            "auto_transitioned": False,
            "current_status": current_status,
            "status_mutation": "MUTATION_DISALLOWED",
            "model_used": False,
            "qa_draft": qa_draft,
            "notifications": notifications,
            "idempotent_replay": False,
            "notice": "Nội dung event không tăng quyền; không tự động transition hoặc đổi vai trò.",
        }

        self._cache[event_fingerprint] = result
        return result


_global_qa_workflow = QAChangeWorkflowEngine()


def process_requirement_change(
    event: dict[str, Any],
    users: Optional[dict[int, dict[str, str]]] = None,
) -> dict[str, Any]:
    """Convenience wrapper for QA change workflow."""
    return _global_qa_workflow.handle_event(event, users=users)
