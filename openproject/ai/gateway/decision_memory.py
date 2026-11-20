"""Decision Memory Engine for QLDAPM Local Second Brain.
Tracks requirement changes, status/gate transitions, and sprint risks with cryptographic provenance.
Strictly forbids external crawling and GitHub research data.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional
from .knowledge_classifier import FORBIDDEN_CRAWL_PATTERN, SecurityValidationError, ALLOWED_PROJECTS

class DecisionType(str, Enum):
    SCOPE_CHANGE = "SCOPE_CHANGE"
    STATUS_GATE = "STATUS_GATE"
    SPRINT_RISK = "SPRINT_RISK"

@dataclass
class DecisionRecord:
    decision_id: str
    project_id: str
    actor_id: int
    decision_type: DecisionType
    summary: str
    reason: str
    native_id: Optional[int]
    lock_version: Optional[int]
    allowed_roles: List[str]
    timestamp: float
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        hasher = hashlib.sha256()
        payload = f"{self.project_id}:{self.actor_id}:{self.decision_type.value}:{self.native_id}:{self.lock_version}:{self.summary}:{self.reason}"
        hasher.update(payload.encode("utf-8"))
        return hasher.hexdigest()

class DecisionMemory:
    def __init__(self):
        self._records: List[DecisionRecord] = []

    def record_decision(
        self,
        project_id: str,
        actor_id: int,
        decision_type: DecisionType,
        summary: str,
        reason: str,
        native_id: Optional[int] = None,
        lock_version: Optional[int] = None,
        allowed_roles: Optional[List[str]] = None,
    ) -> DecisionRecord:
        proj = project_id.strip().upper()
        if proj not in ALLOWED_PROJECTS:
            raise SecurityValidationError(f"Unauthorized project for decision recording: {project_id}")

        # Strict zero-crawler policy check
        if FORBIDDEN_CRAWL_PATTERN.search(summary) or FORBIDDEN_CRAWL_PATTERN.search(reason):
            raise SecurityValidationError("Decisions cannot contain external URLs, GitHub research, or crawler data.")

        roles = allowed_roles if allowed_roles is not None else ["PM", "BA", "FE", "BE", "QA"]
        rec = DecisionRecord(
            decision_id=str(uuid.uuid4()),
            project_id=proj,
            actor_id=actor_id,
            decision_type=decision_type,
            summary=summary.strip(),
            reason=reason.strip(),
            native_id=native_id,
            lock_version=lock_version,
            allowed_roles=roles,
            timestamp=time.time(),
        )
        rec.provenance_hash = rec.compute_hash()
        self._records.append(rec)
        return rec

    def query_decisions(
        self,
        project_id: str,
        role: str,
        decision_type: Optional[DecisionType] = None,
    ) -> List[DecisionRecord]:
        proj = project_id.strip().upper()
        matched: List[DecisionRecord] = []
        for r in self._records:
            if r.project_id != proj:
                continue
            if role not in r.allowed_roles:
                continue
            if decision_type and r.decision_type != decision_type:
                continue
            matched.append(r)
        return matched
