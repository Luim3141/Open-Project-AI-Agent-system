"""Control Center State Module (P08-02):
Provides actor-bound, read-only API data for AI Control Center.
Includes Agent Registry, Task Tree, Progress, and Role Permissions.
Guarantees pagination and strict actor isolation with zero cross-user leakage.
"""
from .permissions import business_manager
from typing import Any
import json
import time

from .agent_models import AgentTask
from .agent_registry import get_agent_registry


def get_agent_tasks_page(store, actor: int, project: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Retrieves paginated agent tasks for the specified actor and project.
    Strictly isolated: never exposes tasks belonging to other actors or other projects.
    """
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or not 0 <= offset <= 2147483647:
        raise ValueError("AGENT_PAGE_LIMIT_1_50_OFFSET_NONNEGATIVE_INT")

    with store.connect() as db:
        total = db.execute(
            "SELECT COUNT(*) FROM agent_tasks WHERE actor=? AND project=?",
            (actor, project)
        ).fetchone()[0]
        rows = db.execute(
            """SELECT id, document, expires FROM agent_tasks
               WHERE actor=? AND project=?
               ORDER BY rowid DESC LIMIT ? OFFSET ?""",
            (actor, project, limit, offset)
        ).fetchall()

    items = []
    now = time.time()
    for row in rows:
        task = AgentTask.from_json(row["document"])
        if (task.task_id, task.actor_id, task.project_id) != (row["id"], actor, project):
            raise ValueError("AGENT_TASK_SCOPE_MISMATCH")
        
        # Present safe summary for Control Center UI
        items.append({
            "task_id": task.task_id,
            "agent": task.agent,
            "run_class": task.run_class,
            "instruction_preview": task.instruction[:100] + ("..." if len(task.instruction) > 100 else ""),
            "created_at": task.created_at,
            "expires_at": task.expires_at,
            "is_expired": task.expires_at <= now,
            "reference_count": len(task.references),
        })

    next_offset = offset + len(items) if offset + len(items) < total else None
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "next_offset": next_offset,
    }


def get_control_center_state(
    store,
    actor_id: int,
    actor_role: str,
    project_id: int,
    limit: int = 20,
    offset: int = 0,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Returns actor-scoped read-only Control Center state.
    - Agent registry: definitions and tools.
    - Progress: paginated agent runs for actor.
    - Task tree: paginated agent tasks for actor.
    - Role permissions: scoped to actor's role.
    """
    config = config or {}
    registry = get_agent_registry()
    agents_summary = []
    for name, agent in registry.list_agents().items():
        agents_summary.append({
            "name": agent.name,
            "role_description": agent.role_description,
            "provider": 'Gemini analysis / local deterministic' if config.get('gemini_multi_agent_enabled') and name!='reviewer' else 'local_deterministic',
            "shares_central_quota": bool(config.get('gemini_multi_agent_enabled') and name!='reviewer'),
            "max_turns": 1 if config.get('gemini_multi_agent_enabled') and name!='reviewer' else 0,
            "max_tokens_per_call": agent.max_tokens_per_call,
            "allowed_tools": list(agent.allowed_tools),
        })

    # Paginated progress
    progress_page = store.agent_runs_page(actor_id, project_id, limit=limit, offset=offset)

    # Paginated task tree
    task_tree_page = get_agent_tasks_page(store, actor_id, project_id, limit=limit, offset=offset)

    # Actor RBAC summary
    is_pm = actor_role == "PM"
    manager = business_manager(actor_role)
    role_info = {
        "actor_id": actor_id,
        "role": actor_role,
        "is_pm": is_pm,
        "is_ai_system_owner": actor_role == "AI_SYSTEM_OWNER",
        "can_mutate_business": manager,
        "scope_policy": "PROJECT_WIDE_VIEW" if manager else "OWN_SCOPE_STRICT",
        "notice": (
            f"Role {actor_role}: duyệt đề xuất của chính mình bằng exact hash; mọi lần ghi cần quyết định riêng."
            if manager else
            f"Role {actor_role}: chỉ đọc, phân tích, đề xuất văn bản và bình luận; không có quyền duyệt ghi nghiệp vụ."
        ),
    }
    from .notification_delivery import status

    return {
        "actor_bound": True,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "project_id": project_id,
        "agent_registry": agents_summary,
        "progress": progress_page,
        "task_tree": task_tree_page,
        "role_permissions": role_info,
        "local_delivery": status(store,actor_id,actor_role,project_id),
    }
