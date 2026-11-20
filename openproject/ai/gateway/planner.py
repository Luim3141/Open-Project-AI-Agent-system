"""Supervisor Planner: separates read vs write, determines dependencies, and allocates model budget."""
import re
import uuid

from .agent_models import AgentTask, ExecutionPlan, PlanBudget, PlanStep

WRITE_TERMS = (
    r"tạo|tạo mới|cập nhật|sửa|thay đổi|gán|phân công|xóa|đổi trạng thái|chuyển trạng thái|đóng|"
    r"create|update|edit|modify|change|assign|delete|remove|close|set status|transition"
)
WRITE_KEYWORDS = re.compile(rf"\b(?:{WRITE_TERMS})\b", re.I)
NEGATED_MUTATIONS = re.compile(
    rf"\b(?:không(?:\s+được)?|đừng|chưa|do\s+not|don['’]t|never)\s+"
    rf"(?:(?:ghi|chỉnh|thực hiện|áp dụng|make|perform|apply)\s+(?:bất kỳ\s+|any\s+)?)?"
    rf"(?:{WRITE_TERMS})\b", re.I,
)

DETERMINISTIC_KEYWORDS = re.compile(
    r"(?i)\b("
    r"đếm|số lượng|tổng số|liệt kê|danh sách|quá hạn|hạn chót|báo cáo hàng ngày|kiểm tra trạng thái|xem|tra cứu|"
    r"count|list|overdue|daily brief|check status|get status|show|view|lookup|summary count"
    r")\b"
)

COMPLEX_ANALYSIS_KEYWORDS = re.compile(
    r"(?i)\b("
    r"phân tích|đánh giá|lý giải|tổng hợp|so sánh|gợi ý|đề xuất|nguy cơ|rủi ro|mâu thuẫn|tiêu chí chấp nhận|"
    r"analyze|analysis|evaluate|reason|synthesize|compare|suggest|recommend|risk|conflict|acceptance criteria|ambiguity"
    r")\b"
)

ROLE_AGENT_MAP = {
    "ba": re.compile(r"(?i)\b(user story|acceptance criteria|ac|yêu cầu|requirement|nghiệp vụ|tính năng|feature|epic)\b"),
    "qa": re.compile(r"(?i)\b(test|test case|kiểm thử|bug|defect|lỗi|regression|triage|kịch bản kiểm thử)\b"),
    "fe": re.compile(r"(?i)\b(frontend|front-end|fe|giao diện|accessibility)\b"),
    "be": re.compile(r"\bBE\b|(?i:\b(backend|back-end|database|schema)\b)"),
    "dev": re.compile(r"(?i)\b(kỹ thuật|technical|api|backend|frontend|fe|be|schema|database|architecture|kiến trúc)\b"),
    "pm": re.compile(r"(?i)\b(sprint|tiến độ|progress|blocker|overdue|trễ hạn|workload|khối lượng|phân bổ|rủi ro)\b"),
}


def is_write_intent(instruction: str) -> bool:
    """Returns True if instruction requests data mutation or state modification."""
    # Ignore only a locally negated verb, never every write because a prompt says "read only".
    # This labels advisory plans; Native permission and consent checks remain authoritative.
    return bool(WRITE_KEYWORDS.search(NEGATED_MUTATIONS.sub("", instruction)))


def is_deterministic_intent(instruction: str) -> bool:
    """Returns True if instruction can be fully answered from native data without model reasoning."""
    if is_write_intent(instruction):
        return False
    if COMPLEX_ANALYSIS_KEYWORDS.search(instruction):
        return False
    return bool(DETERMINISTIC_KEYWORDS.search(instruction))


def is_wbs_planning_intent(instruction: str) -> bool:
    if re.search(r'\b(?:WBS_JSON|WBS_NATIVE_RELATIONS)\b', instruction, re.I):
        return True
    if re.search(r'\b(?:không(?:\s+cần|\s+được)?|đừng|chưa|do not|don[\u2019\']t|never)\s+'
                 r'(?:lập|đề xuất|phân rã|xây dựng|tạo|draft|create|build|propose)\s+'
                 r'(?:(?:một|a|the)\s+)?WBS\b', instruction, re.I):
        return False
    return bool(re.search(r'\bWBS\b', instruction, re.I) and re.search(
        r'\b(?:lập|phân tích|đề xuất|phân rã|xây dựng|tạo|decompose|draft|create|build|propose|analy[sz]e)\b',
        instruction, re.I))


def resolve_target_agent(instruction: str, requested_agent: str) -> str:
    """Resolves the primary specialist agent for domain execution."""
    if requested_agent in {"pm", "ba", "fe", "be", "dev", "qa", "reviewer"}:
        return requested_agent
    for agent, pattern in ROLE_AGENT_MAP.items():
        if pattern.search(instruction):
            return agent
    return "pm"


def resolve_target_agents(instruction: str, requested_agent: str) -> list[str]:
    if requested_agent in {"pm", "ba", "fe", "be", "dev", "qa", "reviewer"}:
        return [requested_agent]
    combined_supervisor = bool(re.search(r'\bPM\s*/\s*Supervisor\b',instruction,re.I))
    instruction = re.sub(r'\bPM\s*/\s*Supervisor\b','Supervisor',instruction,flags=re.I)
    selected = [role for role, pattern in (
        ('ba', r'\bBA\b'), ('fe', r'(?i:\b(FE|frontend|front-end)\b)'), ('be', r'\bBE\b|(?i:\b(backend|back-end)\b)'), ('dev', r'(?i:\b(developer|dev)\b)'),
        ('qa', r'\bQA\b'), ('pm', r'\bPM\b')) if re.search(pattern, instruction)]
    if combined_supervisor and 'pm' in selected:
        selected.remove('pm')
    if {'fe','be'} & set(selected) and 'dev' in selected:
        selected.remove('dev')
    if is_wbs_planning_intent(instruction) and 'ba' not in selected:
        selected.insert(0, 'ba')
    return selected or [resolve_target_agent(instruction, requested_agent)]


def plan_request(task: AgentTask, actor_role: str) -> ExecutionPlan:
    """Decomposes a task into an atomic, typed ExecutionPlan with strict budget and RBAC boundaries."""
    write_intent = is_write_intent(task.instruction)
    deterministic = is_deterministic_intent(task.instruction)
    target_agents = resolve_target_agents(task.instruction, task.agent)

    # 1. Read vs Write separation & RBAC gating
    if write_intent:
        operation_type = "PROPOSAL_WRITE"
        requires_pm_approval = True
    else:
        operation_type = "READ_ONLY"
        requires_pm_approval = False

    # 2. Directed Acyclic Graph (DAG) steps construction
    steps: list[PlanStep] = []
    step_counter = 1

    # Specialists read the same authorized input; only Reviewer consumes all their outputs.
    for target_agent in target_agents:
        steps.append(PlanStep(
            step_id=step_counter,
            agent=target_agent,
            action=f"execute_{target_agent}_domain_task",
            dependencies=[],
            operation_type=operation_type,
            requires_pm_consent=False,
        ))
        step_counter += 1

    # Step 2: Reviewer consistency & RBAC check (runs unless purely deterministic lookup)
    if not deterministic or len(target_agents) > 1:
        steps.append(
            PlanStep(
                step_id=step_counter,
                agent="reviewer",
                action="verify_consistency_and_rbac",
                dependencies=[s.step_id for s in steps],
                operation_type="READ_ONLY",
                requires_pm_consent=False,
            )
        )

    # Step 3: Proposal aggregation for PM approval (only for write proposals)
    if write_intent:
        step_counter += 1
        steps.append(
            PlanStep(
                step_id=step_counter,
                agent="supervisor",
                action="aggregate_pm_mutation_proposal",
                dependencies=[s.step_id for s in steps],
                operation_type="PROPOSAL_WRITE",
                requires_pm_consent=True,
            )
        )

    # 3. Model vs Tool / Deterministic Budget Decision
    if deterministic:
        budget = PlanBudget(
            model_needed=False,
            deterministic_only=True,
            max_turns=0,
            token_estimate=0,
            quota_class=task.run_class,
        )
    else:
        turns = min(len(steps), 2)
        tokens = turns * 800
        budget = PlanBudget(
            model_needed=True,
            deterministic_only=False,
            max_turns=turns,
            token_estimate=tokens,
            quota_class=task.run_class,
        )

    # 4. Construct validated ExecutionPlan
    return ExecutionPlan(
        plan_id=str(uuid.uuid4()),
        task_id=task.task_id,
        actor_id=task.actor_id,
        project_id=task.project_id,
        operation_type=operation_type,
        budget=budget,
        steps=steps,
        requires_pm_approval=requires_pm_approval,
        rejection_reason=None,
    )
