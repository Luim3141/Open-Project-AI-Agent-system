"""Private agent contracts. Scope is evidence to revalidate, never permission or consent."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_AGENT_BYTES = 32768
AgentName = Literal['supervisor','pm','ba','fe','be','dev','qa','reviewer']
Identifier = Annotated[str, Field(pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")]
PositiveId = Annotated[int, Field(gt=0)]
Timestamp = Annotated[float, Field(ge=0)]
RunState = Literal["QUEUED", "RUNNING", "WAITING_QUOTA", "WAITING_PROVIDER", "BLOCKED_KEY_OR_MODEL", "REVIEW", "FAILED", "COMPLETED"]
AGENT_TRANSITIONS = {
    "QUEUED": {"RUNNING", "WAITING_QUOTA", "WAITING_PROVIDER", "BLOCKED_KEY_OR_MODEL", "FAILED"},
    "WAITING_QUOTA": {"QUEUED", "FAILED"},
    "WAITING_PROVIDER": {"QUEUED", "FAILED"},
    "BLOCKED_KEY_OR_MODEL": {"QUEUED", "FAILED"},
    "RUNNING": {"REVIEW", "FAILED", "COMPLETED"},
}


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False,
                              json_schema_extra={"x-max-serialized-bytes": MAX_AGENT_BYTES})
    schema_version: Literal[1] = 1

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version(cls, value):
        if type(value) is not int or value != 1:
            raise ValueError("AGENT_SCHEMA_VERSION_UNSUPPORTED")
        return value

    @model_validator(mode="after")
    def bounded_document(self):
        if len(self.model_dump_json().encode("utf-8")) > MAX_AGENT_BYTES:
            raise ValueError("AGENT_PAYLOAD_TOO_LARGE")
        return self

    @classmethod
    def from_json(cls, body: str | bytes):
        if not isinstance(body, (str, bytes)):
            raise ValueError("AGENT_JSON_REQUIRED")
        if len(body.encode("utf-8") if isinstance(body, str) else body) > MAX_AGENT_BYTES:
            raise ValueError("AGENT_PAYLOAD_TOO_LARGE")
        return cls.model_validate_json(body)


class NativeReference(AgentContract):
    work_package_id: PositiveId
    lock_version: Annotated[int, Field(ge=0)]


class AgentTask(AgentContract):
    task_id: Identifier
    actor_id: PositiveId
    project_id: PositiveId
    conversation_id: Identifier
    agent: AgentName
    instruction: Annotated[str, Field(min_length=1, max_length=8000, pattern=r"\S")]
    references: list[NativeReference] = Field(default_factory=list, max_length=50)
    run_class: Literal["interactive", "agent", "report", "system"] = "agent"
    created_at: Timestamp
    expires_at: Timestamp

    @model_validator(mode="after")
    def ordered_expiry(self):
        if self.expires_at <= self.created_at:
            raise ValueError("AGENT_EXPIRY_INVALID")
        return self


class RunScope(AgentContract):
    run_id: Identifier
    task_id: Identifier
    actor_id: PositiveId
    project_id: PositiveId
    trace_id: Identifier


class AgentResult(RunScope):
    state: Literal["REVIEW", "FAILED", "COMPLETED"]
    summary: Annotated[str, Field(min_length=1, max_length=16000, pattern=r"\S")]
    references: list[NativeReference] = Field(default_factory=list, max_length=50)
    receipt_ids: list[Identifier] = Field(default_factory=list, max_length=100)
    model_used: bool = False
    error_code: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,79}$")] | None = None


class AgentRun(RunScope):
    state: RunState = "QUEUED"
    created_at: Timestamp
    updated_at: Timestamp
    result: AgentResult | None = None

    @model_validator(mode="after")
    def consistent_result(self):
        if self.updated_at < self.created_at:
            raise ValueError("AGENT_RUN_TIME_INVALID")
        if (self.state in {"REVIEW", "FAILED", "COMPLETED"}) != (self.result is not None):
            raise ValueError("AGENT_TERMINAL_RESULT_REQUIRED")
        if self.result is not None:
            for name in RunScope.model_fields:
                if getattr(self, name) != getattr(self.result, name):
                    raise ValueError("AGENT_RESULT_SCOPE_MISMATCH")
            if self.state != self.result.state:
                raise ValueError("AGENT_RESULT_STATE_MISMATCH")
        return self


class AgentProgress(RunScope):
    state: RunState
    created_at: Timestamp
    updated_at: Timestamp
    model_used: bool | None = None
    receipt_id: Identifier | None = None
    can_replay: Literal[False] = False
    reconcile_required: bool = False
    new_request_required: bool = False

    @classmethod
    def from_run(cls, run, receipt_id):
        return cls(**run.model_dump(exclude={"result"}), receipt_id=receipt_id,
            model_used=run.result.model_used if run.result else None,
            reconcile_required=run.state == "FAILED", new_request_required=run.state == "FAILED")


class AgentRunPage(AgentContract):
    items: list[AgentProgress] = Field(max_length=50)
    total: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1, le=50)]
    offset: Annotated[int, Field(ge=0, le=2147483647)]
    next_offset: Annotated[int, Field(ge=0)] | None


class AgentTraceEvent(RunScope):
    event_id: Identifier
    at: Timestamp
    action: Annotated[str, Field(max_length=64)]
    target: Annotated[str, Field(max_length=256)]
    outcome: Annotated[str, Field(max_length=64)]
    version: Annotated[str, Field(max_length=256)] | None = None


class AgentTracePage(AgentContract):
    items: list[AgentTraceEvent] = Field(max_length=50)
    total: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1, le=50)]
    offset: Annotated[int, Field(ge=0, le=2147483647)]
    next_offset: Annotated[int, Field(ge=0)] | None


OperationType = Literal["READ_ONLY", "PROPOSAL_WRITE"]


class PlanStep(AgentContract):
    step_id: PositiveId
    agent: AgentName
    action: Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]
    dependencies: list[PositiveId] = Field(default_factory=list, max_length=10)
    operation_type: OperationType = "READ_ONLY"
    requires_pm_consent: bool = False


class PlanBudget(AgentContract):
    model_needed: bool = False
    deterministic_only: bool = True
    max_turns: Annotated[int, Field(ge=0, le=5)] = 0
    token_estimate: Annotated[int, Field(ge=0, le=16000)] = 0
    quota_class: Literal["interactive", "agent", "report", "system"] = "agent"


class ExecutionPlan(AgentContract):
    plan_id: Identifier
    task_id: Identifier
    actor_id: PositiveId
    project_id: PositiveId
    operation_type: OperationType
    budget: PlanBudget
    steps: list[PlanStep] = Field(default_factory=list, max_length=10)
    requires_pm_approval: bool = False
    rejection_reason: Annotated[str, Field(max_length=256)] | None = None

