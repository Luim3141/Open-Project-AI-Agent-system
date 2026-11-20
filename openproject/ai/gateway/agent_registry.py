"""Agent Registry: Central catalog of all specialized agents in QLDAPM Local V2.
Enforces role-based tool allowlists, model/turn bounds,
Live agents share the central Gemini quota limiter; Reviewer checks local policy only.
"""
from typing import Any, get_args
from pydantic import BaseModel, ConfigDict, Field

from .ba_agent import BAAgent
from .dev_agent import DEVAgent
from .pm_agent import PMAgent
from .qa_agent import QAAgent
from .reviewer_agent import ReviewerAgent
from .planner import plan_request
from .agent_models import AgentTask, RunScope, AgentResult, AgentName

AGENT_NAMES = get_args(AgentName)


def engineering_profile(role: str) -> dict:
    """Project6 execution metadata over the existing role catalog; no second registry."""
    if role not in {'supervisor','pm','ba','dev','reviewer','qa'}:
        raise ValueError('ENGINEERING_ROLE_DENIED')
    get_agent_registry().get_agent(role)
    skill={'supervisor':'planning','pm':'planning','ba':'planning','dev':'development','reviewer':'review','qa':'qa'}[role]
    return {'agent':role,'runtime':'qldapm-supervisor' if role=='supervisor' else 'qldapm-gemini' if role in {'pm','ba'} else 'openclaw',
        'skill':'engineering-'+skill,'version':'1.0.0','project_id':6,
        'responsibilities':{'supervisor':['claim','dependencies','stage handoff','bounded rework','publication and OFF'],
            'pm':['prioritize verified scope','Native backlog/dependencies','assign virtual Dev','blockers and next action'],
            'ba':['functional scope','API behavior','edge cases','acceptance and feedback specification'],
            'dev':['actual source edits','terminal/dependencies','TDD and debugging','receiving feedback'],
            'reviewer':['independent exact-diff review','actionable findings','re-review'],
            'qa':['execute tests','capture real exit/artifacts','defect handoff and retest']}[role],
        'tools':(['existing queue','Native scoped publisher','SecondBrain'] if role=='supervisor' else
            ['shared Gemini structured analysis','Native reads','loaded planning skill'] if role in {'pm','ba'} else
            ['read'] if role=='reviewer' else ['read','exec']),
        'permissions':'Project6/#379 authorized delivery only; host validates Native writes; no MAIN source, merge, credentials or paid fallback',
        'input_contract':'run/task/actor/project + immutable unit + fresh Native version + specification/AC + scoped citations + budget',
        'output_contract':{'supervisor':'durable stage receipt + completion/publication readback',
            'pm':'ordered assignments, dependencies, priorities, blockers, next action + Native backlog readback',
            'ba':'functional specification, API behavior, edge cases, acceptance, source citations',
            'dev':'filesystem diff + command/exit/test artifacts',
            'reviewer':'JSON verdict/findings with exact revision and file/line',
            'qa':'executed command, exit code, acceptance mapping, actual failures'}[role],
        'handoff_condition':'Validated output and checkpoint persisted; errors propagate to bounded rework or OFF; unknown writes require reconciliation',
        'persona':{'supervisor':'bounded ownership/claim/handoff; Paperclip/NEXUS principles',
            'pm':'Senior Project Manager / Sprint Prioritizer','ba':'Requirements Analyst',
            'dev':'Senior Developer / Debugging Specialist','reviewer':'Code Reviewer / Reality Checker',
            'qa':'API Tester / Evidence Collector'}[role]}


class AgentDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: AgentName
    role_description: str
    provider: str = "gemini-shared"
    shares_central_quota: bool = True
    max_turns: int = Field(ge=0, le=2, default=2)
    max_tokens_per_call: int = Field(ge=100, le=4000, default=2000)
    allowed_tools: list[str]
    input_schema: str = 'AgentTask + RunScope + fresh Native references'
    output_schema: str = 'ModelAnalysis -> validated AgentResult'
    context_boundary: str = 'actor/project; at most10visible native IDs and3revalidated knowledge items'
    provider_policy: str = 'FREE_ONLY; shared project budget; no executable model tools'
    max_model_calls_including_retry: int = 2
    timeout_seconds: int = 90
    retry_limit: int = 1
    trace_policy: str = 'durable actor/run/agent provider receipt; no prompts or credentials'


class SupervisorHandler:
    """Lightweight handler for Supervisor planning and orchestration."""

    def run(self, task: AgentTask, scope: RunScope, packages: list[dict[str, Any]] | None = None) -> AgentResult:
        plan = plan_request(task, actor_role="PM")
        summary = (
            f"### KẾ HOẠCH ĐIỀU PHỐI (EXECUTION PLAN) — {plan.plan_id}\n"
            f"- **Loại tác vụ:** {plan.operation_type}\n"
            f"- **Ngân sách:** Model needed: {plan.budget.model_needed}, Turns: {plan.budget.max_turns}\n"
            f"- **Số bước:** {len(plan.steps)}\n"
            f"- **Yêu cầu PM duyệt:** {plan.requires_pm_approval}\n"
        )
        return AgentResult(
            run_id=scope.run_id,
            task_id=scope.task_id,
            actor_id=scope.actor_id,
            project_id=scope.project_id,
            trace_id=scope.trace_id,
            state="COMPLETED",
            summary=summary,
            references=[],
            receipt_ids=[],
            model_used=False,
        )


REGISTRY_CONFIG: dict[str, AgentDefinition] = {
    "supervisor": AgentDefinition(
        name="supervisor",
        role_description="Điều phối tổng thể, lập kế hoạch tác vụ (Plan DAG) và tổng hợp proposal",
        provider="gemini-shared",
        shares_central_quota=True,
        max_turns=2,
        max_tokens_per_call=2000,
        allowed_tools=["plan_request", "aggregate_proposal", "dispatch_agent"],
    ),
    "pm": AgentDefinition(
        name="pm",
        role_description="Quản lý tiến độ dự án, rủi ro Sprint, công việc quá hạn và khối lượng tải (Workload)",
        provider="gemini-shared",
        shares_central_quota=True,
        max_turns=2,
        max_tokens_per_call=2000,
        allowed_tools=["analyze_overdue", "analyze_blockers", "analyze_workload", "analyze_sprint_risks"],
    ),
    "ba": AgentDefinition(
        name="ba",
        role_description="Phân tích nghiệp vụ, chuẩn hóa User Stories, tiêu chí chấp nhận (AC) và phát hiện mơ hồ",
        provider="gemini-shared",
        shares_central_quota=True,
        max_turns=2,
        max_tokens_per_call=2000,
        allowed_tools=["draft_user_story", "draft_ac", "detect_ambiguity", "draft_dependencies"],
    ),
    "fe": AgentDefinition(name='fe',role_description='Frontend live specialist: interaction, accessibility, UI state and API integration; local shared technical advisory only',
        allowed_tools=['get_work_package','knowledge_search']),
    "be": AgentDefinition(name='be',role_description='Backend live specialist: API, authorization, validation, transactions and failure handling; local shared technical advisory only',
        allowed_tools=['get_work_package','knowledge_search']),
    "dev": AgentDefinition(
        name="dev",
        role_description="Phân tích kỹ thuật, phân rã FE/BE, hợp đồng API và rủi ro kiến trúc/đồng thời",
        provider="gemini-shared",
        shares_central_quota=True,
        max_turns=2,
        max_tokens_per_call=2000,
        allowed_tools=["breakdown_fe_be", "identify_dependencies", "evaluate_technical_risks"],
    ),
    "qa": AgentDefinition(
        name="qa",
        role_description="Bảo đảm chất lượng, thiết kế ca kiểm thử, phát hiện khoảng trống hồi quy và triage lỗi",
        provider="gemini-shared",
        shares_central_quota=True,
        max_turns=2,
        max_tokens_per_call=2000,
        allowed_tools=["generate_test_cases", "detect_regression_gaps", "triage_bug", "evaluate_test_attestation"],
    ),
    "reviewer": AgentDefinition(
        name="reviewer",
        role_description="Kiểm định độc lập, đối chiếu bằng chứng native, phát hiện xung đột và rà soát RBAC",
        provider="local-policy",
        shares_central_quota=False,
        max_model_calls_including_retry=0,
        max_turns=1,
        max_tokens_per_call=1500,
        allowed_tools=["verify_evidence", "detect_conflicts", "check_rbac"],
    ),
}


class AgentRegistry:
    """Central registry maintaining agent definitions, tool permissions, and shared quota constraints."""

    def __init__(self, user_map=None):
        self._agents = dict(REGISTRY_CONFIG)
        self._handlers = {
            "supervisor": SupervisorHandler(),
            "pm": PMAgent(user_map),
            "ba": BAAgent(),
            "fe": DEVAgent('fe'),
            "be": DEVAgent('be'),
            "dev": DEVAgent(),
            "qa": QAAgent(),
            "reviewer": ReviewerAgent(),
        }

    def list_agents(self) -> dict[str, AgentDefinition]:
        return dict(self._agents)

    def get_agent(self, name: str) -> AgentDefinition:
        if name not in self._agents:
            raise ValueError(f"AGENT_UNKNOWN: {name}")
        return self._agents[name]

    def get_handler(self, name: str) -> Any:
        if name not in self._handlers:
            raise ValueError(f"AGENT_HANDLER_UNKNOWN: {name}")
        return self._handlers[name]


_GLOBAL_REGISTRY = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """Returns singleton AgentRegistry instance."""
    return _GLOBAL_REGISTRY
