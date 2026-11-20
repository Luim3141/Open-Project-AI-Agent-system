"""Append-only, code/ID-only telemetry. Stored outputs remain in ai_runs.result."""
import time
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .agent_trace import current_run
from .agent_models import AgentName

EventType = Literal['REQUEST_RECEIVED','AUTHORIZED','QUEUED','PLANNING_STARTED','PLAN_CREATED',
    'AGENT_ASSIGNED','AGENT_STARTED','MODEL_REQUEST_STARTED','MODEL_RESPONSE_RECEIVED',
    'AGENT_COMPLETED','AGENT_FAILED','RETRY_SCHEDULED','REVIEW_STARTED','REVIEW_COMPLETED',
    'RESULT_AGGREGATED','RESULT_AVAILABLE','PROPOSAL_CREATED','APPROVAL_REQUIRED','RUN_COMPLETED','RUN_FAILED']


class ExecutionEvent(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True,allow_inf_nan=False)
    schema_version: Literal[1]=1
    event_id: str
    run_id: str
    trace_id: str
    event_type: EventType
    agent_id: AgentName | None=None
    step_id: int | None=Field(default=None,ge=1,le=10)
    timestamp: float=Field(ge=0)
    sequence: int=Field(ge=1)
    status: Literal['QUEUED','PLANNING','RUNNING','REVIEWING','COMPLETED','FAILED','REVIEW'] | None=None
    receipt_id: str | None=None
    phase: Literal['countTokens','generateContent'] | None=None
    attempt: int | None=Field(default=None,ge=0,le=1)
    http_status: int | None=Field(default=None,ge=100,le=599)
    error_code: str | None=Field(default=None,pattern=r'^[A-Z][A-Z0-9_]{0,79}$')


def append(db,scope,event_type,agent=None,step_id=None,status=None,key=None,**metadata):
    identifier=str(uuid.uuid5(uuid.UUID(scope.run_id),key)) if key else str(uuid.uuid4())
    event=ExecutionEvent(event_id=identifier,run_id=scope.run_id,trace_id=scope.trace_id,
        event_type=event_type,agent_id=agent,step_id=step_id,timestamp=time.time(),sequence=1,status=status,**metadata)
    db.execute('INSERT OR IGNORE INTO execution_events(event_id,run_id,actor,project,document) VALUES(?,?,?,?,?)',
        (identifier,scope.run_id,scope.actor_id,scope.project_id,event.model_dump_json()))
    from .n8n_lifecycle_outbox import enqueue
    enqueue(db,scope,event)


def emit(event_type,agent=None,step_id=None,status=None,key=None,**metadata):
    binding=current_run.get()
    if not binding:return
    store,scope=binding
    with store.connect() as db:append(db,scope,event_type,agent,step_id,status,key,**metadata)

