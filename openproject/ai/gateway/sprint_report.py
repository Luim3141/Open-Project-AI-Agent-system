"""Deterministic Sprint Report Generator (P07-01 under CR-USER-CAPACITY-20).
Provides read-only, deterministic-first sprint snapshot metrics for 1 to 20 users without calling LLMs.
Includes:
- Work package counts (open, closed, total, completion percentage)
- Status and work package type distributions
- Overdue tasks with days overdue and native lock_version references
- Blockers and blocker dependency links
- Multi-user workload distribution (supporting 1-20 users across roles)
- Fail-closed role scoping: PM gets full project overview; non-PM gets scoped perspective
- Process-focused metrics with required disclaimers (not individual performance ranking)
- Cryptographic SHA256 fingerprint for integrity and stale detection
"""
from .permissions import business_manager
from datetime import date, datetime, timezone, timedelta
import hashlib
import json
import re
from typing import Any

from .store import canonical, digest

CLOSED_STATUSES = {"DONE", "CLOSED", "RESOLVED", "REJECTED", "HOÀN THÀNH", "ĐÃ ĐÓNG"}


def _get_status(package: dict[str, Any]) -> str:
    links = package.get("_links", {})
    if "status" in links and "title" in links["status"]:
        return str(links["status"]["title"]).strip()
    return str(package.get("status", "")).strip()


def _is_closed(package: dict[str, Any]) -> bool:
    status = _get_status(package).upper()
    return status in CLOSED_STATUSES


def _get_type(package: dict[str, Any]) -> str:
    links = package.get("_links", {})
    if "type" in links and "title" in links["type"]:
        return str(links["type"]["title"]).strip()
    return str(package.get("type", "Task")).strip()


def _get_assignee(package: dict[str, Any]) -> tuple[int | None, str]:
    links = package.get("_links", {})
    if "assignee" in links:
        href = (links.get('assignee') or {}).get('href') or ''
        title = (links.get('assignee') or {}).get('title') or 'Unassigned'
        match = re.search(r"/users/(\d+)", href)
        if match:
            return int(match.group(1)), title
    return None, "Unassigned"


def _get_due_date(package: dict[str, Any]) -> date | None:
    raw = package.get("dueDate") or package.get("due_date")
    if raw and isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    return None


def blocker_evidence(package, packages, relations=None):
    """Separate explicit block declarations from unresolved scheduling prerequisites."""
    by_id = {p['id']: p for p in packages}
    identifier = package['id']
    blocked_ids, prerequisites, relation_ids, blocker_relation_ids = set(), set(), set(), set()
    for row in relations or []:
        endpoints = [re.fullmatch(r'/api/v3/work_packages/(\d+)',
            (row.get('_links', {}).get(key) or {}).get('href') or '') for key in ('from', 'to')]
        if not all(endpoints):
            continue
        source, target = (int(match[1]) for match in endpoints)
        if source not in by_id or target not in by_id or source == target:
            continue
        kind = row.get('type')
        dependent, prerequisite = (target, source) if kind in {'blocks','precedes'} else (source, target)
        if dependent != identifier or _is_closed(by_id[prerequisite]):
            continue
        if kind in {'blocks','blocked'}:
            blocked_ids.add(prerequisite)
            blocker_relation_ids.add(row['id'])
        elif kind in {'precedes','follows'}:
            prerequisites.add(prerequisite)
            relation_ids.add(row['id'])
    description = package.get('description') or ''
    description = description.get('raw') or '' if isinstance(description, dict) else str(description)
    # shortcut: prose is only a declaration when a line begins with an explicit block phrase; prefer Native relations.
    declarations = re.findall(r'(?im)^\s*(?:(?:đang )?bị chặn(?: bởi)?|blocked(?: by)?)(?:\s|:)([^\n.;]*)', description)
    status_blocked = _get_status(package).upper() in {'BLOCKED','BỊ CHẶN'}
    subject_blocked = '[BLOCKED]' in package.get('subject','').upper()
    for clause in declarations:
        blocked_ids.update(int(i) for i in re.findall(r'#(\d+)',clause)
            if int(i) in by_id and int(i) != identifier and not _is_closed(by_id[int(i)]))
    return {'blocked': status_blocked or subject_blocked or bool(declarations) or bool(blocked_ids),
        'blocker_ids': sorted(blocked_ids), 'prerequisite_ids': sorted(prerequisites),
        'relation_ids': sorted(relation_ids), 'blocker_relation_ids': sorted(blocker_relation_ids),
        'evidence_sources': (['NATIVE_STATUS'] if status_blocked else []) +
            (['SUBJECT_MARKER'] if subject_blocked else []) + (['PROSE_DECLARATION'] if declarations else []) +
            (['NATIVE_BLOCK_RELATION'] if blocker_relation_ids else [])}


def generate_sprint_report(
    packages: list[dict[str, Any]],
    as_of_date: date | None = None,
    user_map: dict[int, dict[str, str]] | None = None,
    actor_id: int | None = None,
    actor_role: str = "PM",
    project_id: int = 3,
    relations: list[dict[str, Any]] | None = None,
    dependency_packages: list[dict[str, Any]] | None = None,
    sprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generates a complete, deterministic, read-only sprint report with role-based scoping."""
    if as_of_date is None:
        as_of_date = datetime.now(timezone(timedelta(hours=7))).date()

    users = user_map or {}
    total_packages = len(packages)
    closed_packages = sum(1 for p in packages if _is_closed(p))
    open_packages = total_packages - closed_packages
    progress_percent = round((closed_packages / total_packages * 100), 1) if total_packages > 0 else 0.0

    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    overdue_all: list[dict[str, Any]] = []
    blocked_all: list[dict[str, Any]] = []
    dependencies_all: list[dict[str, Any]] = []
    unassigned_open = 0
    missing_due_open = 0

    pkg_by_id = {p["id"]: p for p in packages}

    for p in packages:
        status = _get_status(p)
        p_type = _get_type(p)
        by_status[status] = by_status.get(status, 0) + 1
        by_type[p_type] = by_type.get(p_type, 0) + 1

        is_open = not _is_closed(p)
        assignee_id, assignee_name = _get_assignee(p)
        due = _get_due_date(p)

        if is_open:
            if assignee_id is None:
                unassigned_open += 1
            if due is None:
                missing_due_open += 1

            # Check overdue
            if due and due < as_of_date:
                days = (as_of_date - due).days
                overdue_all.append({
                    "id": p["id"],
                    "lockVersion": p.get("lockVersion", 1),
                    "subject": p.get("subject", ""),
                    "status": status,
                    "assignee": assignee_name,
                    "assignee_id": assignee_id,
                    "due_date": due.isoformat(),
                    "days_overdue": days,
                })

            # Check blocked
            subject = p.get("subject", "")
            evidence = blocker_evidence(p, packages if dependency_packages is None else dependency_packages, relations)
            if evidence['prerequisite_ids']:
                dependencies_all.append({'id':p['id'],'prerequisite_ids':evidence['prerequisite_ids'],
                    'relation_ids':evidence['relation_ids']})
            if evidence['blocked']:
                blocked_all.append({
                    "id": p["id"],
                    "lockVersion": p.get("lockVersion", 1),
                    "subject": subject,
                    "status": status,
                    "assignee": assignee_name,
                    "assignee_id": assignee_id,
                    "blocker_ids": evidence['blocker_ids'],
                    "blocker_relation_ids": evidence['blocker_relation_ids'],
                    "evidence_sources": evidence['evidence_sources'],
                })

    overdue_all.sort(key=lambda x: x["days_overdue"], reverse=True)

    # Workload calculation across team members (supports 1 to 20 users)
    workload_summary: dict[str, Any] = {}
    for uid, uinfo in users.items():
        uname = uinfo.get("name", f"User {uid}")
        urole = uinfo.get("role", "Unknown")
        assigned_pkgs = [p for p in packages if not _is_closed(p) and _get_assignee(p)[0] == uid]
        workload_summary[str(uid)] = {
            "user_id": uid,
            "name": uname,
            "role": urole,
            "open_count": len(assigned_pkgs),
            "package_ids": [p["id"] for p in assigned_pkgs],
        }

    # Unassigned open tasks
    unassigned_pkgs = [p for p in packages if not _is_closed(p) and _get_assignee(p)[0] is None]
    workload_summary["unassigned"] = {
        "open_count": len(unassigned_pkgs),
        "package_ids": [p["id"] for p in unassigned_pkgs],
    }

    # Role-based scoping:
    # PM sees all team workload and all overdue items.
    # Non-PM sees project summary counts, but personal workload and personal overdue only.
    if business_manager(actor_role):
        visible_overdue = overdue_all
        visible_blocked = blocked_all
        visible_workload = workload_summary
    else:
        visible_overdue = [item for item in overdue_all if item["assignee_id"] == actor_id]
        visible_blocked = [item for item in blocked_all if item["assignee_id"] == actor_id]
        visible_workload = {
            str(actor_id): workload_summary.get(str(actor_id), {
                "user_id": actor_id,
                "open_count": 0,
                "package_ids": [],
            }),
            "project_totals": {
                "total_open": open_packages,
                "total_closed": closed_packages,
                "unassigned": unassigned_open,
            },
        }

    # Sprint Health assessment
    health_reasons = []
    if len(overdue_all) > 0:
        health_reasons.append(f"Có {len(overdue_all)} công việc quá hạn cần xử lý.")
    if len(blocked_all) > 0:
        health_reasons.append(f"Có {len(blocked_all)} công việc bị chặn (blocked).")
    if unassigned_open > 0:
        health_reasons.append(f"Có {unassigned_open} công việc chưa phân công người thực hiện.")
    if missing_due_open > 0:
        health_reasons.append(f"Có {missing_due_open} công việc chưa có thời hạn hoàn thành (deadline).")

    if len(overdue_all) > 3 or len(blocked_all) > 2:
        health_status = "CRITICAL"
    elif len(overdue_all) > 0 or len(blocked_all) > 0 or unassigned_open > 2:
        health_status = "AT_RISK"
    else:
        health_status = "UNKNOWN" if relations is None else "ON_TRACK"
        if not health_reasons:
            health_reasons.append("Không phát hiện cảnh báo theo các quy tắc đã kiểm tra; chưa phải cam kết tiến độ Sprint.")

    report_body = {
        "summary": {
            "total_packages": total_packages,
            "closed_packages": closed_packages,
            "open_packages": open_packages,
            "progress_percent": progress_percent,
            "by_status": by_status,
            "by_type": by_type,
            "unassigned_open_count": unassigned_open,
            "missing_deadline_open_count": missing_due_open,
        },
        "sprint_health": {
            "status": health_status,
            "reasons": health_reasons,
        },
        "overdue": visible_overdue,
        "blocked": visible_blocked,
        "dependencies": [entry for entry in dependencies_all if business_manager(actor_role) or
            _get_assignee(pkg_by_id[entry['id']])[0] == actor_id],
        "dependency_data_quality": 'UNAVAILABLE' if relations is None else 'NATIVE_RELATIONS_READ',
        "scope": 'CURRENT_VISIBLE_PROJECT_WORK_PACKAGES',
        "workload": visible_workload,
        "limitations": [
            "Chỉ số quy trình dự án phục vụ hỗ trợ ra quyết định, không xếp hạng cá nhân",
            "Thuần túy tính toán tất định (deterministic), không tiêu tốn token LLM",
            ("Đã chọn Sprint Native; chưa có capacity hoặc commitment baseline để dự báo tiến độ." if sprint is not None else
             "Chưa chọn Sprint Native; ngưỡng rủi ro là heuristic trên snapshot dự án hiện tại, không phải dự báo tiến độ."),
            "follows/precedes là dependency lịch trình, không tự coi là trạng thái BLOCKED. Relation snapshot không được revalidate khi đọc báo cáo cũ.",
        ],
    }

    if sprint is not None:
        report_body.update(scope='NATIVE_SPRINT_WORK_PACKAGES', native_sprint=sprint)
    report_fingerprint = digest(canonical(report_body))

    return {
        "state": "READY",
        "as_of_date": as_of_date.isoformat(),
        "project_id": project_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "model_used": False,
        "observed_at": datetime.now(timezone(timedelta(hours=7))).timestamp(),
        "fingerprint": report_fingerprint,
        "report": report_body,
    }
