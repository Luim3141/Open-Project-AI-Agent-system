"""PM Agent: Evaluates Sprint risks, work packages overdue, blockers, and workload with evidence.
Strictly read-only / advisory: never self-updates OpenProject tasks.
"""
from datetime import date, datetime, timezone, timedelta
import re
from typing import Any

from .agent_models import AgentResult, AgentTask, NativeReference, RunScope
from .planner import is_write_intent
from .sprint_report import blocker_evidence

CLOSED_STATUSES = {"DONE", "CLOSED", "RESOLVED", "REJECTED", "HOÀN THÀNH", "ĐÃ ĐÓNG"}

DEFAULT_USER_MAP = {
    7: {"name": "Project Manager", "role": "PM"},
    6: {"name": "BA Specialist", "role": "BA"},
    8: {"name": "BE Developer", "role": "BE"},
    9: {"name": "FE Developer", "role": "FE"},
    10: {"name": "QA Engineer", "role": "QA"},
}


def _get_status(package: dict[str, Any]) -> str:
    """Extracts status title from package dictionary."""
    links = package.get("_links", {})
    if "status" in links and "title" in links["status"]:
        return str(links["status"]["title"]).strip()
    return str(package.get("status", "")).strip()


def _is_closed(package: dict[str, Any]) -> bool:
    """Returns True if work package is in a completed or closed state."""
    status = _get_status(package).upper()
    return status in CLOSED_STATUSES


def _get_assignee(package: dict[str, Any]) -> tuple[int | None, str]:
    """Returns (assignee_id, assignee_name) from package links."""
    links = package.get("_links", {})
    if "assignee" in links:
        href = (links.get('assignee') or {}).get('href') or ''
        title = (links.get('assignee') or {}).get('title') or 'Unassigned'
        match = re.search(r"/users/(\d+)", href)
        if match:
            return int(match.group(1)), title
    return None, "Unassigned"


def _get_due_date(package: dict[str, Any]) -> date | None:
    """Parses due date from package."""
    raw = package.get("dueDate") or package.get("due_date")
    if raw and isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    return None


def analyze_overdue(packages: list[dict[str, Any]], as_of_date: date) -> tuple[list[dict[str, Any]], list[NativeReference]]:
    """Identifies open work packages past due date with native references."""
    overdue_items = []
    references = []
    for p in packages:
        if _is_closed(p):
            continue
        due = _get_due_date(p)
        if due and due < as_of_date:
            days = (as_of_date - due).days
            ref = NativeReference(work_package_id=p["id"], lock_version=p["lockVersion"])
            overdue_items.append({"package": p, "days_overdue": days, "due_date": due, "reference": ref})
            references.append(ref)
    overdue_items.sort(key=lambda x: x["days_overdue"], reverse=True)
    return overdue_items, references


def analyze_blockers(packages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[NativeReference]]:
    """Identifies blocked work packages and extracts referenced blocker packages."""
    blocked_items = []
    ref_map: dict[int, NativeReference] = {}
    pkg_by_id = {p["id"]: p for p in packages}

    for p in packages:
        status = _get_status(p).upper()
        evidence = blocker_evidence(p, packages)
        is_blocked = evidence['blocked']

        if is_blocked and not _is_closed(p):
            ref = NativeReference(work_package_id=p["id"], lock_version=p["lockVersion"])
            ref_map[p["id"]] = ref
            blocker_ids = evidence['blocker_ids']
            for bid in blocker_ids:
                if bid in pkg_by_id:
                    ref_map[bid] = NativeReference(work_package_id=bid, lock_version=pkg_by_id[bid]["lockVersion"])

            blocked_items.append({
                "package": p,
                "status": status,
                "blocker_ids": blocker_ids,
                "reference": ref,
            })

    return blocked_items, list(ref_map.values())


def analyze_workload(
    packages: list[dict[str, Any]],
    user_map: dict[int, dict[str, str]] | None = None,
) -> tuple[dict[int, list[dict[str, Any]]], list[NativeReference]]:
    """Calculates active workload distribution across team members."""
    users = user_map or DEFAULT_USER_MAP
    workload: dict[int, list[dict[str, Any]]] = {uid: [] for uid in users}
    workload[0] = []  # unassigned
    references = []

    for p in packages:
        if _is_closed(p):
            continue
        uid, _ = _get_assignee(p)
        bucket = uid if uid in workload else 0
        workload[bucket].append(p)
        references.append(NativeReference(work_package_id=p["id"], lock_version=p["lockVersion"]))

    return workload, references


def analyze_sprint_risks(
    packages: list[dict[str, Any]],
    as_of_date: date,
    user_map: dict[int, dict[str, str]] | None = None,
) -> tuple[str, list[NativeReference], dict[str, Any]]:
    """Comprehensive Sprint delivery risk assessment combining overdue, blockers, and workload."""
    overdue_items, overdue_refs = analyze_overdue(packages, as_of_date)
    blocked_items, blocker_refs = analyze_blockers(packages)
    workload, workload_refs = analyze_workload(packages, user_map)

    total_count = len(packages)
    closed_count = sum(1 for p in packages if _is_closed(p))
    open_count = total_count - closed_count

    # Risk level determination based on factual metrics
    if len(blocked_items) >= 1 or len(overdue_items) >= 2:
        risk_level = "CAO"
    elif len(overdue_items) == 1:
        risk_level = "TRUNG BÌNH"
    else:
        risk_level = "THẤP"

    # Merge references preserving uniqueness
    ref_dict: dict[int, NativeReference] = {}
    for r in overdue_refs + blocker_refs:
        ref_dict[r.work_package_id] = r

    lines = [
        f"### ĐÁNH GIÁ TỔNG THỂ RỦI RO SPRINT (Mức độ: {risk_level})",
        f"- **Tổng số công việc:** {total_count} (Hoàn thành: {closed_count}, Đang mở: {open_count})",
        f"- **Công việc quá hạn:** {len(overdue_items)}",
        f"- **Công việc bị chặn (Blocker):** {len(blocked_items)}",
        "",
        "#### Chi tiết rủi ro và bằng chứng:",
    ]

    if overdue_items:
        lines.append("**1. Công việc quá hạn:**")
        for item in overdue_items:
            pkg = item["package"]
            lines.append(f"  - #{pkg['id']}: {pkg['subject']} (Quá hạn {item['days_overdue']} ngày, Hạn: {item['due_date']})")

    if blocked_items:
        lines.append("**2. Điểm nghẽn (Blocker):**")
        for item in blocked_items:
            pkg = item["package"]
            blockers_str = ", ".join(f"#{bid}" for bid in item["blocker_ids"]) if item["blocker_ids"] else "Chưa rõ mã"
            lines.append(f"  - #{pkg['id']} [BLOCKED]: {pkg['subject']} (Bị chặn bởi: {blockers_str})")

    lines.append("\n#### Khuyến nghị hành động:")
    lines.append("1. Ưu tiên giải tỏa blocker cho các công việc có mức độ ưu tiên cao.")
    lines.append("2. Điều chỉnh phân bổ nguồn lực hoặc đàm phán phạm vi cho các mục trễ hạn.")

    summary = "\n".join(lines)
    return summary, list(ref_dict.values()), {"risk_level": risk_level, "overdue_count": len(overdue_items), "blocked_count": len(blocked_items)}


class PMAgent:
    """PM Agent specialist providing evidence-based Sprint risk, overdue, and workload analysis.

    Enforces strict read-only/advisory contract: never mutates tasks directly.
    """

    def __init__(self, user_map: dict[int, dict[str, str]] | None = None):
        self.user_map = user_map or DEFAULT_USER_MAP

    def run(
        self,
        task: AgentTask,
        scope: RunScope,
        packages: list[dict[str, Any]],
        as_of_date: date | None = None,
        provider=None,
    ) -> AgentResult:
        if provider is not None:
            return provider.run_agent('pm',task,scope,packages)
        as_of = as_of_date or datetime.now(timezone(timedelta(hours=7))).date()
        instruction = task.instruction

        # STRICT RULE: Refuse direct task updates; PM Agent is strictly advisory / read-only
        if is_write_intent(instruction):
            # Extract cited IDs from instruction or task references
            pkg_map = {p["id"]: p for p in packages}
            cited_ids = [int(m) for m in re.findall(r"#(\d+)", instruction)]
            references = []
            for cid in cited_ids:
                if cid in pkg_map:
                    references.append(NativeReference(work_package_id=cid, lock_version=pkg_map[cid]["lockVersion"]))
            if not references and task.references:
                references = list(task.references)

            summary = (
                "PM Agent chỉ phân tích dữ liệu và đề xuất phương án, tuyệt đối KHÔNG tự ý cập nhật hay chỉnh sửa "
                "trực tiếp các công việc (work packages) trong OpenProject. "
                "Yêu cầu sửa đổi đã được ghi nhận và chuyển thành bản dự thảo đề xuất (Proposal Draft) cần phê duyệt "
                "bởi người dùng PM theo chính sách PM-only-write trước khi thực hiện bất kỳ thao tác ghi nào.\n"
                f"- Các công việc liên quan: {', '.join(f'#{r.work_package_id} (lock_version: {r.lock_version})' for r in references)}"
            )

            return AgentResult(
                run_id=scope.run_id,
                task_id=scope.task_id,
                actor_id=scope.actor_id,
                project_id=scope.project_id,
                trace_id=scope.trace_id,
                state="REVIEW",
                summary=summary,
                references=references,
                receipt_ids=[],
                model_used=False,
            )

        # READ / ANALYSIS FLOW
        instr_lower = instruction.lower()

        if "rủi ro" in instr_lower or "risk" in instr_lower:
            summary, references, _ = analyze_sprint_risks(packages, as_of, self.user_map)

        elif "quá hạn" in instr_lower or "overdue" in instr_lower:
            overdue_items, references = analyze_overdue(packages, as_of)
            lines = [f"### BÁO CÁO CÔNG VIỆC QUÁ HẠN (Tính đến ngày {as_of.isoformat()})"]
            lines.append(f"Tìm thấy **{len(overdue_items)}** công việc quá hạn trong dự án:\n")
            for item in overdue_items:
                p = item["package"]
                lines.append(f"- **#{p['id']}**: {p['subject']}")
                lines.append(f"  - Hạn chót: {item['due_date']} (Quá hạn {item['days_overdue']} ngày)")
                lines.append(f"  - Tiến độ: {p.get('percentageDone', 0)}% | Trạng thái: {_get_status(p)}")
            summary = "\n".join(lines)

        elif "nghẽn" in instr_lower or "blocker" in instr_lower or "cản trở" in instr_lower:
            blocked_items, references = analyze_blockers(packages)
            lines = [f"### BÁO CÁO ĐIỂM NGHẼN VÀ BLOCKER (Tính đến ngày {as_of.isoformat()})"]
            lines.append(f"Tìm thấy **{len(blocked_items)}** công việc đang bị chặn hoặc gây cản trở:\n")
            for item in blocked_items:
                p = item["package"]
                blockers_str = ", ".join(f"#{bid}" for bid in item["blocker_ids"]) if item["blocker_ids"] else "Chưa xác định"
                lines.append(f"- **#{p['id']}** [BLOCKED]: {p['subject']}")
                lines.append(f"  - Công việc chặn: {blockers_str}")
                lines.append(f"  - Người phụ trách: {_get_assignee(p)[1]}")
            summary = "\n".join(lines)

        elif "workload" in instr_lower or "khối lượng" in instr_lower or "phân bổ" in instr_lower:
            workload, references = analyze_workload(packages, self.user_map)
            lines = ["### BÁO CÁO PHÂN BỔ KHỐI LƯỢNG CÔNG VIỆC (WORKLOAD)"]
            for uid, user_info in self.user_map.items():
                assigned_pkgs = workload.get(uid, [])
                pkg_list_str = ", ".join(f"#{p['id']}" for p in assigned_pkgs) if assigned_pkgs else "Không có task mở"
                lines.append(f"- **{user_info['role']} ({user_info['name']})**: {len(assigned_pkgs)} công việc mở ({pkg_list_str})")
            if workload.get(0):
                unassigned_str = ", ".join(f"#{p['id']}" for p in workload[0])
                lines.append(f"- **Chưa phân công (Unassigned)**: {len(workload[0])} công việc ({unassigned_str})")
            summary = "\n".join(lines)

        else:
            summary, references, _ = analyze_sprint_risks(packages, as_of, self.user_map)

        return AgentResult(
            run_id=scope.run_id,
            task_id=scope.task_id,
            actor_id=scope.actor_id,
            project_id=scope.project_id,
            trace_id=scope.trace_id,
            state="COMPLETED",
            summary=summary,
            references=references,
            receipt_ids=[],
            model_used=False,
        )
