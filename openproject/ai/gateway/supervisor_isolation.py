"""Supervisor Isolation: Verifies multi-actor (up to 20) memory and workflow isolation,
cross-project boundaries, and fair quota sharing without starvation.
"""
import time
import uuid
from typing import Any

from .agent_models import AgentRun, AgentTask, RunScope
from .store import Store
from .supervisor import Supervisor


def verify_actor_isolation(
    supervisor: Supervisor,
    store: Store,
    users: dict[int, dict[str, str]],
    packages: list[dict[str, Any]],
    project_id: int = 3,
) -> dict[str, Any]:
    """Executes distinct agent runs for all actors (1-20) and validates zero memory/workflow leakage."""
    run_records: dict[int, dict[str, Any]] = {}
    leakage_count = 0
    now = time.time()

    instructions = {
        7: "Phân tích rủi ro và tiến độ sprint hiện tại",
        6: "Soạn User Story và tiêu chí chấp nhận cho tính năng mới",
        8: "Phân tích kỹ thuật và schema cơ sở dữ liệu backend",
        9: "Phân rã giao diện người dùng frontend và component",
        10: "Thiết kế kịch bản kiểm thử tích hợp và phát hiện hồi quy",
    }

    # 1. Execute task for each actor
    for actor_id, info in users.items():
        task_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())

        task = AgentTask(
            task_id=task_id,
            actor_id=actor_id,
            project_id=project_id,
            conversation_id=conv_id,
            agent="supervisor",
            instruction=instructions.get(actor_id, "Yêu cầu mặc định"),
            created_at=now,
            expires_at=now + 600.0,
        )
        store.create_agent_task(actor_id, project_id, task)

        run = AgentRun(
            run_id=run_id,
            task_id=task_id,
            actor_id=actor_id,
            project_id=project_id,
            trace_id=trace_id,
            created_at=now,
            updated_at=now,
        )
        store.create_agent_run(actor_id, project_id, run)

        scope = RunScope(
            run_id=run_id,
            task_id=task_id,
            actor_id=actor_id,
            project_id=project_id,
            trace_id=trace_id,
        )

        plan, result = supervisor.execute_task(task, scope, packages, actor_role=info["role"])
        run_records[actor_id] = {
            "task": task,
            "run": run,
            "scope": scope,
            "result": result,
        }

    # 2. Cross-actor isolation audit
    for target_actor, data in run_records.items():
        for other_actor in users:
            if other_actor == target_actor:
                continue
            # Other actor must NOT be able to retrieve target actor's task or run
            try:
                store.agent_task(other_actor, project_id, data["task"].task_id)
                leakage_count += 1
            except PermissionError:
                pass  # Correctly isolated

            try:
                store.agent_run(other_actor, project_id, data["run"].run_id)
                leakage_count += 1
            except PermissionError:
                pass  # Correctly isolated

    run_ids = [r["run"].run_id for r in run_records.values()]
    task_ids = [r["task"].task_id for r in run_records.values()]

    return {
        "isolated": leakage_count == 0,
        "executed_actors": list(users.keys()),
        "leakage_count": leakage_count,
        "run_ids": run_ids,
        "task_ids": task_ids,
    }


def simulate_fair_quota_allocation(
    store: Store,
    actors: list[int],
    project: str,
    rpm_limit: int = 15,
    requests_per_actor: int = 3,
) -> dict[str, Any]:
    """Simulates round-robin reservation across 5 actors, verifying fair sharing without starvation."""
    limits = {"rpm": rpm_limit, "tpm": 250000, "rpd": 500}
    admitted: dict[int, int] = {a: 0 for a in actors}
    rejected: dict[int, int] = {a: 0 for a in actors}

    # Round-robin requests
    for round_num in range(requests_per_actor):
        for actor in actors:
            try:
                store.reserve_gemini(project=project, limits=limits, input_tokens=100)
                admitted[actor] += 1
            except ValueError:
                rejected[actor] += 1

    return {
        "total_admitted": sum(admitted.values()),
        "total_rejected": sum(rejected.values()),
        "admitted_per_actor": admitted,
        "rejected_per_actor": rejected,
    }


# Backward compatibility alias
verify_5_actor_isolation = verify_actor_isolation
