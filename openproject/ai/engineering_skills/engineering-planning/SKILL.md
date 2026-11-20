---
name: engineering-planning
description: Refine a scoped requirement into one engineering unit, acceptance criteria, dependencies and a verifiable implementation plan.
metadata:
  version: 1.0.0
---

ID `qldapm.plan.v1`; version `1.0.0`. Local adaptation of Superpowers brainstorming/writing-plans and Agency Agents senior PM, sprint prioritizer and requirements analyst responsibilities.

Inputs: fresh Native requirement/version, actor/project, repo revision and scoped citations. Tools: existing QLDAPM registry PM/BA handlers and Native reads. Trigger: Supervisor planning before an admitted unit.

Resolve the objective and constraints from evidence. Split into independently testable units, identify dependencies and prioritize one. Define API behavior, edge cases and an AC-to-test mapping. Keep simulated estimates separate from measured work. Output the task/spec hash, plan and acceptance contract. Escalate material ambiguity; do not invent assignees or completion. Verification is performed by the Supervisor against the approved unit and fresh Native source. Planning may be deterministic; report `model_used=false` when no inference occurred.
