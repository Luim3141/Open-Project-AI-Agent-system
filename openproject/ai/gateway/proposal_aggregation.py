"""Proposal Aggregation: Aggregates multi-agent change requests into formal proposals,
enforces strict PM-only approval gates, and guarantees readback verification.
"""
import time
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from .store import Store, canonical, digest


class AggregatedProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    proposal_id: str
    proposer_actor_id: int
    target_work_package_id: int
    current_lock_version: int
    proposed_changes: dict[str, Any]
    reason: str
    preview_diff: str
    preview_hash: str
    requires_pm_approval: bool = True
    created_at: float
    expires_at: float


def aggregate_mutation_proposal(
    proposer_actor_id: int,
    target_work_package_id: int,
    current_lock_version: int,
    changes: dict[str, Any],
    reason: str,
    native_package: dict[str, Any],
    store: Store,
) -> AggregatedProposal:
    """Aggregates a requested change into a typed, hashed Proposal awaiting PM consent."""
    proposal_id = str(uuid.uuid4())
    now = time.time()
    expires_at = now + 900.0  # 15 minutes TTL

    # Format human-readable diff
    diff_lines = [
        f"### ĐỀ XUẤT THAY ĐỔI CÔNG VIỆC #{target_work_package_id}",
        f"- **Người đề xuất:** Actor #{proposer_actor_id}",
        f"- **Lý do đề xuất:** {reason}",
        f"- **Phiên bản khóa hiện tại (lockVersion):** {current_lock_version}",
        "",
        "#### Chi tiết các trường thay đổi:",
    ]
    for key, new_val in changes.items():
        old_val = native_package.get(key, "N/A")
        diff_lines.append(f"  - `{key}`: {old_val} => **{new_val}**")

    preview_diff = "\n".join(diff_lines)

    # Compute stable preview SHA256
    fingerprint = digest(canonical({
        "proposal_id": proposal_id,
        "pid": target_work_package_id,
        "lock": current_lock_version,
        "changes": changes,
        "proposer": proposer_actor_id,
    }))

    payload = {
        "action": "update_work_package",
        "arguments": {
            "id": target_work_package_id,
            "lock_version": current_lock_version,
            "changes": changes,
            "reason": reason,
        },
        "preview": preview_diff,
        "preview_hash": fingerprint,
    }

    # Persist in central store proposals table
    with store.connect() as db:
        db.execute(
            "INSERT INTO proposals (id, actor, payload, hash, expires, state, result) VALUES (?, ?, ?, ?, ?, 'pending', NULL)",
            (proposal_id, proposer_actor_id, canonical(payload), fingerprint, expires_at),
        )

    return AggregatedProposal(
        proposal_id=proposal_id,
        proposer_actor_id=proposer_actor_id,
        target_work_package_id=target_work_package_id,
        current_lock_version=current_lock_version,
        proposed_changes=changes,
        reason=reason,
        preview_diff=preview_diff,
        preview_hash=fingerprint,
        requires_pm_approval=True,
        created_at=now,
        expires_at=expires_at,
    )


def approve_and_execute_proposal(
    actor_id: int,
    actor_role: str,
    proposal_id: str,
    preview_hash: str,
    store: Store,
    native: Any,
) -> dict[str, Any]:
    """Legacy demo executor is intentionally closed; only Service.confirm may execute writes."""
    raise PermissionError('CANONICAL_GATEWAY_CONFIRM_REQUIRED; untrusted role arguments cannot grant approval')
