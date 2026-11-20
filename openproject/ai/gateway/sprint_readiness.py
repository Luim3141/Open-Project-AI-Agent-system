"""Sprint Readiness Review Workflow (P07-05 under CR-USER-CAPACITY-20).
Inspects work packages for Sprint readiness:
1. Missing Acceptance Criteria (AC / DoR).
2. Missing test coverage (QA test work packages or test criteria).
3. Blocked dependencies (prerequisites not completed).

Guarantees:
- Output identifies exact Work Package IDs with lockVersion.
- Strictly Advisory: Generates structured proposals for PM review; NEVER auto-writes.
- Pure Deterministic: 0 LLM tokens, 100% native rules.
- Multi-user / multi-role aware (PM, BA, FE, BE, QA).
"""
import re
from typing import Any, Optional

from .sprint_report import (
    blocker_evidence,
    _get_status,
    _is_closed,
    _get_type,
    _get_assignee,
)
from .decision_memory import DecisionMemory, DecisionType

AC_PATTERN = re.compile(
    r"(acceptance\s*criteria|tiêu\s*chí\s*chấp\s*nhận|\bAC\s*:|\[\s*[x ]\s*\]|given\s+.*when\s+.*then)",
    re.IGNORECASE,
)
TEST_TYPE_PATTERN = re.compile(r"(test|kiểm\s*thử|qa)", re.IGNORECASE)


class SprintReadinessEngine:
    def __init__(self, decision_memory: Optional[DecisionMemory] = None):
        self.decision_memory = decision_memory

    def evaluate(
        self,
        packages: list[dict[str, Any]],
        project_id: str = "QLDAPM",
    ) -> dict[str, Any]:
        pkg_by_id = {p["id"]: p for p in packages}
        active_packages = [p for p in packages if not _is_closed(p)]

        # Map parent-child relationships and tests
        tests_for_parent: dict[int, list[int]] = {}
        for p in packages:
            p_type = _get_type(p)
            subject = p.get("subject", "")
            is_test = bool(TEST_TYPE_PATTERN.search(p_type) or TEST_TYPE_PATTERN.search(subject))
            if is_test:
                parent_href = (p.get("_links", {}).get("parent") or {}).get("href") or ''
                match = re.search(r"/work_packages/(\d+)", parent_href)
                if match:
                    parent_id = int(match.group(1))
                    tests_for_parent.setdefault(parent_id, []).append(p["id"])

        missing_ac_packages: list[dict[str, Any]] = []
        missing_test_packages: list[dict[str, Any]] = []
        blocked_packages: list[dict[str, Any]] = []
        ready_packages: list[dict[str, Any]] = []

        for p in active_packages:
            pid = p["id"]
            subject = p.get("subject", "")
            status = _get_status(p)
            p_type = _get_type(p)
            lock_version = p.get("lockVersion", 1)
            assignee_id, assignee_name = _get_assignee(p)
            desc = (
                p.get("description", {}).get("raw", "")
                if isinstance(p.get("description"), dict)
                else str(p.get("description", ""))
            )

            is_test_itself = bool(TEST_TYPE_PATTERN.search(p_type) or TEST_TYPE_PATTERN.search(subject))

            has_issues = False

            # 1. AC check (only for non-test work packages)
            if not is_test_itself:
                has_ac = bool(AC_PATTERN.search(desc))
                if not has_ac:
                    missing_ac_packages.append({
                        "id": pid,
                        "lockVersion": lock_version,
                        "subject": subject,
                        "type": p_type,
                        "status": status,
                        "assignee": assignee_name,
                        "reason": "Thiếu Tiêu chí chấp nhận (Acceptance Criteria / AC)",
                    })
                    has_issues = True

            # 2. Test coverage check (only for user stories, features, development tasks)
            if not is_test_itself:
                has_test_link = pid in tests_for_parent and len(tests_for_parent[pid]) > 0
                has_test_in_desc = "kiểm thử" in desc.lower() or "test case" in desc.lower()
                if not (has_test_link or has_test_in_desc):
                    missing_test_packages.append({
                        "id": pid,
                        "lockVersion": lock_version,
                        "subject": subject,
                        "type": p_type,
                        "status": status,
                        "assignee": assignee_name,
                        "reason": "Chưa có liên kết task kiểm thử (QA Test) hoặc kịch bản test",
                    })
                    has_issues = True

            # 3. Blocked dependency check
            evidence = blocker_evidence(p, packages)
            is_blocked = evidence['blocked']
            if is_blocked:
                valid_blockers = evidence['blocker_ids']
                # Check if blockers are unresolved
                unresolved_blockers = [
                    bid for bid in valid_blockers if not _is_closed(pkg_by_id[bid])
                ]
                blocked_packages.append({
                    "id": pid,
                    "lockVersion": lock_version,
                    "subject": subject,
                    "type": p_type,
                    "status": status,
                    "assignee": assignee_name,
                    "blocker_ids": unresolved_blockers or valid_blockers,
                    "reason": f"Bị chặn bởi các công việc chưa hoàn thành: {unresolved_blockers or valid_blockers}",
                })
                has_issues = True

            if not has_issues and not is_test_itself:
                ready_packages.append({
                    "id": pid,
                    "subject": subject,
                    "type": p_type,
                })

        # Structured proposals for PM review
        proposals_for_pm: list[dict[str, Any]] = []

        if missing_ac_packages:
            proposals_for_pm.append({
                "action": "ADD_ACCEPTANCE_CRITERIA",
                "target_package_ids": [p["id"] for p in missing_ac_packages],
                "recommended_owner_role": "BA",
                "proposal": (
                    f"Có {len(missing_ac_packages)} công việc thiếu Tiêu chí chấp nhận (AC). "
                    f"Đề xuất PM giao BA bổ sung AC trước khi đưa vào Sprint."
                ),
            })

        if missing_test_packages:
            proposals_for_pm.append({
                "action": "CREATE_TEST_TASKS",
                "target_package_ids": [p["id"] for p in missing_test_packages],
                "recommended_owner_role": "QA",
                "proposal": (
                    f"Có {len(missing_test_packages)} công việc chưa có test task đi kèm. "
                    f"Đề xuất PM giao QA tạo task kiểm thử tương ứng."
                ),
            })

        if blocked_packages:
            proposals_for_pm.append({
                "action": "RESOLVE_BLOCKERS",
                "target_package_ids": [p["id"] for p in blocked_packages],
                "recommended_owner_role": "PM",
                "proposal": (
                    f"Có {len(blocked_packages)} công việc đang bị chặn (blocked). "
                    f"Đề xuất PM ưu tiên gỡ vướng mắc hoặc hoãn đưa vào Sprint."
                ),
            })

        total_dev_scope = len(active_packages) - sum(
            1 for p in active_packages if bool(TEST_TYPE_PATTERN.search(_get_type(p)))
        )
        total_dev_scope = max(1, total_dev_scope)
        readiness_pct = round((len(ready_packages) / total_dev_scope) * 100, 1)

        total_issues = len(missing_ac_packages) + len(missing_test_packages) + len(blocked_packages)
        if total_issues == 0:
            readiness_status = "READY_FOR_SPRINT"
        elif total_issues <= 2:
            readiness_status = "NEEDS_ATTENTION"
        else:
            readiness_status = "NOT_READY"

        # Record risk decision if memory is present and critical issues found
        if self.decision_memory and total_issues > 0:
            try:
                self.decision_memory.record_decision(
                    project_id=project_id,
                    actor_id=1,
                    decision_type=DecisionType.SPRINT_RISK,
                    summary=f"Sprint readiness flagged {total_issues} issues",
                    reason=f"Status: {readiness_status}. Missing AC: {len(missing_ac_packages)}, Missing Test: {len(missing_test_packages)}, Blocked: {len(blocked_packages)}",
                    allowed_roles=["PM", "BA", "QA"],
                )
            except Exception:
                pass

        return {
            "state": "READY",
            "project_id": project_id,
            "advisory_only": True,
            "auto_executed": False,
            "model_used": False,
            "notice": "Chỉ đề xuất để PM duyệt, không tự động ghi dữ liệu vào OpenProject.",
            "sprint_readiness": {
                "status": readiness_status,
                "readiness_percentage": readiness_pct,
                "total_issues": total_issues,
            },
            "missing_ac_count": len(missing_ac_packages),
            "missing_ac_packages": missing_ac_packages,
            "missing_test_count": len(missing_test_packages),
            "missing_test_packages": missing_test_packages,
            "blocked_count": len(blocked_packages),
            "blocked_packages": blocked_packages,
            "ready_packages_count": len(ready_packages),
            "ready_packages": ready_packages,
            "proposals_for_pm": proposals_for_pm,
            "limitations": [
                "Báo cáo chất lượng chuẩn bị Sprint phục vụ hỗ trợ ra quyết định",
                "Thuần túy tính toán tất định, không tiêu tốn token LLM",
            ],
        }


def evaluate_sprint_readiness(
    packages: list[dict[str, Any]],
    project_id: str = "QLDAPM",
    decision_memory: Optional[DecisionMemory] = None,
) -> dict[str, Any]:
    """Convenience function to evaluate sprint readiness."""
    engine = SprintReadinessEngine(decision_memory=decision_memory)
    return engine.evaluate(packages, project_id=project_id)
