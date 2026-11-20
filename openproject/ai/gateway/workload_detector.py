"""Workload Skew and Missing Owner/Deadline Detection Workflow (P07-04 under CR-USER-CAPACITY-20).
Provides deterministic detection of:
1. Workload imbalance (skew) across team members within role groups (supporting 1-20 users).
2. Unassigned open work packages.
3. Open work packages missing deadlines (due dates).

Guarantees:
- Strictly Advisory: Generates suggestions only; NEVER auto-assigns or mutates native records.
- Deterministic-first: Pure native calculation, 0 LLM calls, zero Gemini API tokens.
- Scale: Fully supports 1 to 20 users across multiple roles (PM, BA, FE, BE, QA).
- Ethical Compliance: Process-focused indicators for decision support, not employee ranking.
"""
from typing import Any

from .sprint_report import (
    _get_status,
    _is_closed,
    _get_type,
    _get_assignee,
    _get_due_date,
)


def detect_workload_imbalance(
    packages: list[dict[str, Any]],
    users: dict[int, dict[str, str]],
    project_id: int = 3,
) -> dict[str, Any]:
    """Analyzes workload distribution, detects skew and missing owners/deadlines."""
    active_packages = [p for p in packages if not _is_closed(p)]

    unassigned_tasks: list[dict[str, Any]] = []
    missing_deadline_tasks: list[dict[str, Any]] = []
    task_count_by_user: dict[int, int] = {int(uid): 0 for uid in users}
    task_ids_by_user: dict[int, list[int]] = {int(uid): [] for uid in users}

    for p in active_packages:
        pid = p["id"]
        lock_version = p.get("lockVersion", 1)
        subject = p.get("subject", "")
        status = _get_status(p)
        p_type = _get_type(p)
        assignee_id, assignee_name = _get_assignee(p)
        due = _get_due_date(p)

        if assignee_id is None:
            unassigned_tasks.append({
                "id": pid,
                "lockVersion": lock_version,
                "subject": subject,
                "type": p_type,
                "status": status,
                "due_date": due.isoformat() if due else None,
            })
        else:
            if assignee_id in task_count_by_user:
                task_count_by_user[assignee_id] += 1
                task_ids_by_user[assignee_id].append(pid)

        if due is None:
            missing_deadline_tasks.append({
                "id": pid,
                "lockVersion": lock_version,
                "subject": subject,
                "type": p_type,
                "status": status,
                "assignee": assignee_name,
                "assignee_id": assignee_id,
            })

    # Group users by role
    users_by_role: dict[str, list[int]] = {}
    member_workloads: dict[str, Any] = {}

    for uid_int, uinfo in users.items():
        uid_str = str(uid_int)
        role = uinfo.get("role", "Unknown")
        name = uinfo.get("name", f"User {uid_int}")
        users_by_role.setdefault(role, []).append(uid_int)
        member_workloads[uid_str] = {
            "user_id": uid_int,
            "name": name,
            "role": role,
            "task_count": task_count_by_user.get(uid_int, 0),
            "package_ids": task_ids_by_user.get(uid_int, []),
        }

    # Skew analysis within each role group
    skew_analysis: dict[str, Any] = {}
    suggestions: list[dict[str, Any]] = []

    for role, uids in users_by_role.items():
        if len(uids) < 2:
            continue

        loads = [task_count_by_user.get(uid, 0) for uid in uids]
        max_load = max(loads)
        min_load = min(loads)
        avg_load = round(sum(loads) / len(loads), 1)

        # Flag skew if max_load - min_load >= 3 and max_load > 0
        has_skew = (max_load - min_load >= 3) and (max_load > 0)
        skew_analysis[role] = {
            "role": role,
            "member_count": len(uids),
            "max_load": max_load,
            "min_load": min_load,
            "avg_load": avg_load,
            "has_skew": has_skew,
        }

        if has_skew:
            max_uid = [uid for uid in uids if task_count_by_user.get(uid, 0) == max_load][0]
            min_uid = [uid for uid in uids if task_count_by_user.get(uid, 0) == min_load][0]
            max_name = users[max_uid].get("name", f"User {max_uid}")
            min_name = users[min_uid].get("name", f"User {min_uid}")

            suggestions.append({
                "type": "REBALANCE_WORKLOAD",
                "role": role,
                "priority": "HIGH" if max_load >= 4 else "MEDIUM",
                "source_user_id": max_uid,
                "source_user_name": max_name,
                "target_user_id": min_uid,
                "target_user_name": min_name,
                "message": (
                    f"Thành viên {max_name} ({role}) đang đảm nhận {max_load} việc "
                    f"trong khi có thành viên khác ({min_name}) có {min_load} việc. "
                    f"Gợi ý PM xem xét điều chuyển bớt công việc."
                ),
            })

    # Suggestions for unassigned tasks
    if unassigned_tasks:
        suggestions.append({
            "type": "ASSIGN_UNOWNED_TASKS",
            "priority": "HIGH",
            "task_ids": [t["id"] for t in unassigned_tasks],
            "message": f"Có {len(unassigned_tasks)} công việc chưa có người phụ trách (unassigned). Gợi ý PM xem xét giao việc.",
        })

    # Suggestions for missing deadlines
    if missing_deadline_tasks:
        suggestions.append({
            "type": "SET_DEADLINES",
            "priority": "MEDIUM",
            "task_ids": [t["id"] for t in missing_deadline_tasks],
            "message": f"Có {len(missing_deadline_tasks)} công việc chưa xác định hạn chót (dueDate). Gợi ý PM và các lead thiết lập deadline cho Sprint.",
        })

    return {
        "state": "READY",
        "project_id": project_id,
        "advisory_only": True,
        "auto_assigned": False,
        "model_used": False,
        "notice": "Chỉ mang tính chất tư vấn đề xuất, chỉ PM mới có quyền thực thi thay đổi trên OpenProject.",
        "unassigned_tasks_count": len(unassigned_tasks),
        "unassigned_tasks": unassigned_tasks,
        "missing_deadline_tasks_count": len(missing_deadline_tasks),
        "missing_deadline_tasks": missing_deadline_tasks,
        "member_workloads": member_workloads,
        "skew_analysis": skew_analysis,
        "suggestions": suggestions,
        "limitations": [
            "Chỉ số quy trình nội bộ hỗ trợ quản lý dự án, tuyệt đối không dùng để đánh giá năng lực hay xếp hạng nhân viên",
            "Tính toán tất định từ dữ liệu native, không gọi mô hình AI và không tự động phân công",
        ],
    }


def generate_workload_suggestions(
    packages: list[dict[str, Any]],
    users: dict[int, dict[str, str]],
    project_id: int = 3,
) -> dict[str, Any]:
    """Convenience wrapper for workload detection."""
    return detect_workload_imbalance(packages, users, project_id=project_id)
