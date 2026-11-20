"""Supervisor: Multi-agent orchestrator executing bounded DAG plans,

selective agent dispatch, 5-actor isolation, and PM proposal gating.
Strictly respects Gemini shared quota and prohibits wide fanout storms.
"""
from typing import Any
import copy
import time

from .agent_models import AgentResult, AgentTask, ExecutionPlan, RunScope, PlanBudget, NativeReference
from .agent_registry import AgentRegistry, get_agent_registry
from .planner import plan_request
from .permissions import require
from .presentation import requested_ids, safe_text
from .execution_events import emit


class Supervisor:
    """Bounded multi-agent supervisor orchestrating domain specialists and the independent reviewer."""

    def __init__(self, registry: AgentRegistry | None = None, qa_report=None):
        self.registry = registry or get_agent_registry()
        self.qa_report=qa_report
        self.outputs=[]

    def execute_task(
        self,
        task: AgentTask,
        scope: RunScope,
        packages: list[dict[str, Any]],
        actor_role: str = "PM",
        progress=None,
        provider=None,
    ) -> tuple[ExecutionPlan, AgentResult]:
        """Decomposes, selectively dispatches, and aggregates multi-agent results within bounded graph."""
        require(actor_role, 'analyze')
        if any(getattr(task, key) != getattr(scope, key) for key in ('task_id','actor_id','project_id')):
            raise PermissionError('SUPERVISOR_SCOPE_MISMATCH')
        if task.expires_at <= time.time():
            raise ValueError('AGENT_TASK_EXPIRED')
        package_map = {p['id']:p for p in packages}
        selected = set(requested_ids(task.instruction)) | {r.work_package_id for r in task.references}
        if selected - package_map.keys():
            raise PermissionError('AGENT_REFERENCE_NOT_VISIBLE')
        if any(package_map[r.work_package_id]['lockVersion'] != r.lock_version for r in task.references):
            raise ValueError('AGENT_REFERENCE_STALE')
        total = len(packages)
        packages = copy.deepcopy([p for p in packages if not selected or p['id'] in selected][:10])
        for package in packages:
            package['subject'] = safe_text(package.get('subject'))[:512]
            description = package.get('description') or {}
            package['description'] = {'raw': safe_text(description.get('raw','') if isinstance(description,dict) else description)[:4000]}
        if provider is not None:
            self.outputs=provider.outputs
            return provider.execute(self.registry,task,scope,packages,actor_role,progress)
        # Native ACL filtering precedes this bounded, local analysis.
        plan = plan_request(task, actor_role=actor_role)
        emit('PLANNING_STARTED',agent='supervisor',status='PLANNING')
        emit('PLAN_CREATED',agent='supervisor',status='COMPLETED')
        for step in plan.steps:emit('AGENT_ASSIGNED',agent=step.agent,step_id=step.step_id,status='QUEUED')
        plan.budget = PlanBudget(quota_class=task.run_class)

        # 2. Sequential / Bounded Step Execution
        step_results: list[AgentResult] = []
        self.outputs=step_results

        completed = set()
        for step in plan.steps:
            if not set(step.dependencies) <= completed:
                raise ValueError('AGENT_DEPENDENCY_NOT_COMPLETED')
            if time.time() >= task.expires_at:
                raise ValueError('AGENT_TASK_EXPIRED')
            if progress:
                progress(plan, step, step_results)
            emit('REVIEW_STARTED' if step.agent=='reviewer' else 'AGENT_STARTED',agent=step.agent,step_id=step.step_id,status='REVIEWING' if step.agent=='reviewer' else 'RUNNING')
            if step.agent in {"pm", "ba", "fe", "be", "dev", "qa"}:
                handler = self.registry.get_handler(step.agent)
                if step.agent=='qa' and self.qa_report is not None:
                    result=handler.run(task,scope,packages,verified_report=self.qa_report)
                else:
                    result=handler.run(task,scope,packages)
                step_results.append(result)

            elif step.agent == "reviewer":
                rev_handler = self.registry.get_handler("reviewer")
                rev_result = rev_handler.run(task, scope, step_results, packages)
                step_results.append(rev_result)

            elif step.agent == "supervisor":
                step_results.append(AgentResult(**scope.model_dump(), state='REVIEW',
                    summary='Đề xuất tổng hợp đang chờ PM phê duyệt qua luồng preview/confirm của Gateway; chưa có native mutation.',
                    references=step_results[0].references))
            completed.add(step.step_id)
            emit('REVIEW_COMPLETED' if step.agent=='reviewer' else 'AGENT_COMPLETED',agent=step.agent,step_id=step.step_id,status=step_results[-1].state)

        # 3. Aggregation & State Synthesis
        if not step_results:
            # Fallback for empty step execution
            handler = self.registry.get_handler(plan.steps[0].agent if plan.steps else "pm")
            step_results.append(handler.run(task, scope, packages))

        primary_result = step_results[0]
        reviewer_result = step_results[1] if len(step_results) > 1 else None

        # Determine terminal state (REVIEW if write intent/proposal, else COMPLETED)
        if any(r.state == 'FAILED' for r in step_results):
            final_state = 'FAILED'
        elif plan.operation_type == "PROPOSAL_WRITE" or any(r.state == "REVIEW" for r in step_results):
            final_state = "REVIEW"
        else:
            final_state = "COMPLETED"

        # Synthesize narrative summary and dedup references
        if reviewer_result:
            final_summary = '\n\n---\n'.join(r.summary for r in step_results)
            ref_dict = {r.work_package_id: r for result in step_results for r in result.references}
        else:
            final_summary = primary_result.summary
            ref_dict = {r.work_package_id: r for r in primary_result.references}

        # Input provenance is separate from semantic acceptance of the generated draft.
        for package in packages:
            ref_dict.setdefault(package['id'],NativeReference(work_package_id=package['id'],lock_version=package['lockVersion']))
        final_result = AgentResult(
            run_id=scope.run_id,
            task_id=scope.task_id,
            actor_id=scope.actor_id,
            project_id=scope.project_id,
            trace_id=scope.trace_id,
            state=final_state,
            summary=(f'Phân tích local trên {len(packages)}/{total} công việc trong phạm vi phân tích; tối đa 10 mục/lượt.\n'
                     'Kết quả là bản phân tích/dự thảo, chưa thay đổi dữ liệu native.\n' + final_summary)[:8000],
            references=list(ref_dict.values()),
            receipt_ids=[],
            model_used=any(r.model_used for r in step_results),
            error_code='AGENT_REVIEW_FAILED' if final_state == 'FAILED' else None,
        )
        emit('RESULT_AGGREGATED',agent='supervisor',status=final_result.state)

        return plan, final_result
