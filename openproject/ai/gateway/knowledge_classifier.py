"""Internal Knowledge Classifier for QLDAPM Local Second Brain.
Enforces project isolation, native provenance, and strict zero-crawler policies.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re
from typing import Any, Dict, List, Optional, Set

ALLOWED_PROJECTS: Set[str] = {"QAG3", "DEMO", "DEMO-PROJECT", "QLDAPM", "QLDAPM-LOCAL", "3"}

# Strict pattern to prevent external web crawlers, GitHub research, or URL indexing
FORBIDDEN_CRAWL_PATTERN = re.compile(
    r"(?:https?://|github\.com|git\s+clone|crawler|scraper|spider|web\s+research)",
    re.IGNORECASE,
)

class KnowledgeDocType(str, Enum):
    ARCHITECTURE = "ARCHITECTURE"
    ADR = "ADR"
    WORK_PACKAGE = "WORK_PACKAGE"
    ACCEPTANCE_CRITERIA = "ACCEPTANCE_CRITERIA"
    COMMENT = "COMMENT"
    SPRINT_REPORT = "SPRINT_REPORT"

class SecurityValidationError(ValueError):
    """Raised when knowledge document violates security boundary or crawler policy."""
    pass

@dataclass
class KnowledgeDocument:
    doc_type: KnowledgeDocType
    project_id: str
    source_id: str
    title: str
    content: str
    source_hash: str
    allowed_roles: List[str] = field(default_factory=lambda: ["PM", "BA", "FE", "BE", "QA"])
    metadata: Dict[str, Any] = field(default_factory=dict)

def _compute_hash(content: str, doc_type: str, source_id: str, project_id: str = '') -> str:
    # Deterministic SHA256 content hash with provenance salt
    hasher = hashlib.sha256()
    hasher.update(f"{project_id}:{doc_type}:{source_id}:{content.strip()}".encode("utf-8"))
    return hasher.hexdigest()

def classify_document(
    doc_type: KnowledgeDocType,
    project_id: str,
    source_id: str,
    title: str,
    content: str,
    allowed_roles: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> KnowledgeDocument:
    if not project_id or (project_id.strip().upper() not in ALLOWED_PROJECTS and not re.fullmatch(r'[1-9][0-9]*',project_id)):
        raise SecurityValidationError(f"Unauthorized or invalid project_id: {project_id}")

    # Enforce strictly internal knowledge only - no external web crawls or github research
    if FORBIDDEN_CRAWL_PATTERN.search(source_id) or FORBIDDEN_CRAWL_PATTERN.search(content):
        raise SecurityValidationError("External crawling, GitHub research, and external URLs are strictly forbidden.")

    roles = allowed_roles if allowed_roles is not None else ["PM", "BA", "FE", "BE", "QA"]
    meta = metadata.copy() if metadata else {}
    doc_hash = _compute_hash(content, doc_type.value, source_id, project_id.strip().upper())

    return KnowledgeDocument(
        doc_type=doc_type,
        project_id=project_id.strip().upper(),
        source_id=source_id,
        title=title.strip(),
        content=content.strip(),
        source_hash=doc_hash,
        allowed_roles=roles,
        metadata=meta,
    )

def classify_work_package_knowledge(wp: Dict[str, Any]) -> List[KnowledgeDocument]:
    project_id = str(wp.get("project_id", "")).strip().upper()
    if not project_id or project_id not in ALLOWED_PROJECTS:
        raise SecurityValidationError(f"Work Package has unauthorized project_id: {project_id}")

    wp_id = wp.get("id")
    lock_version = wp.get("lock_version", 1)
    subject = wp.get("subject", "Work Package")
    description = wp.get("description", "")

    docs: List[KnowledgeDocument] = []
    base_meta = {
        "native_id": wp_id,
        "lock_version": lock_version,
        "type": wp.get("type", "Task"),
        "status": wp.get("status", "Active"),
    }

    # 1. Main Work Package Document
    wp_doc = classify_document(
        doc_type=KnowledgeDocType.WORK_PACKAGE,
        project_id=project_id,
        source_id=f"wp:{wp_id}",
        title=f"WP #{wp_id}: {subject}",
        content=f"{subject}\n\n{description}",
        metadata=base_meta,
    )
    docs.append(wp_doc)

    # 2. Extract Acceptance Criteria if present in Gherkin or Given-When-Then format
    ac_match = re.search(r"(?:Given|Khi|Khi mà|AC|Acceptance Criteria).*?(?:Then|Thì)", description, re.IGNORECASE | re.DOTALL)
    if ac_match or "given" in description.lower():
        ac_doc = classify_document(
            doc_type=KnowledgeDocType.ACCEPTANCE_CRITERIA,
            project_id=project_id,
            source_id=f"wp:{wp_id}:ac",
            title=f"AC for WP #{wp_id}: {subject}",
            content=description,
            metadata=base_meta,
        )
        docs.append(ac_doc)

    # 3. Extract Comments / Journal Notes
    comments = wp.get("comments", [])
    for idx, c in enumerate(comments):
        c_id = c.get("id", idx + 1)
        author = c.get("author", "Unknown")
        c_text = c.get("text", "")
        c_meta = base_meta.copy()
        c_meta.update({"comment_id": c_id, "author": author})
        c_doc = classify_document(
            doc_type=KnowledgeDocType.COMMENT,
            project_id=project_id,
            source_id=f"wp:{wp_id}:comment:{c_id}",
            title=f"Comment #{c_id} on WP #{wp_id} by {author}",
            content=c_text,
            metadata=c_meta,
        )
        docs.append(c_doc)

    return docs
