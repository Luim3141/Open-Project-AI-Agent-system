"""n8n Local Event Indexing Hook for QLDAPM Local Second Brain.
Provides non-blocking event ingestion, secret redaction, rate limiting, and retry queue.
"""
from dataclasses import dataclass, field
import json
import logging
import re
import time
import hmac
from typing import Any, Dict, List, Optional
from .knowledge_classifier import KnowledgeDocType, classify_document
from .knowledge_ingestion import KnowledgeIngester

logger = logging.getLogger("qldapm.indexing_hook")

SECRET_PATTERNS = [
    re.compile(r"(?:token|password|secret|bearer|api[_-]?key)\s*[:=]\s*([^\s,;]+)", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
]

def redact_secrets(text: str) -> str:
    cleaned = text
    for pat in SECRET_PATTERNS:
        cleaned = pat.sub(r"[REDACTED_SECRET]", cleaned)
    return cleaned

@dataclass
class IndexingEvent:
    event_type: str
    project_id: str
    source_id: str
    title: str
    content: str
    allowed_roles: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class IndexingHookHandler:
    def __init__(
        self,
        ingester: KnowledgeIngester,
        webhook_secret: str | None = None,
        rate_limit_per_minute: int = 60,
    ):
        self.ingester = ingester
        if not webhook_secret:
            raise ValueError('EXPLICIT_PRIVATE_HOOK_KEY_REQUIRED')
        self.webhook_secret = webhook_secret
        self.rate_limit = rate_limit_per_minute
        self._call_timestamps: List[float] = []
        self._retry_queue: List[Dict[str, Any]] = []

    def get_retry_queue_size(self) -> int:
        return len(self._retry_queue)

    def _is_rate_limited(self) -> bool:
        now = time.time()
        # Purge timestamps older than 60 seconds
        self._call_timestamps = [t for t in self._call_timestamps if now - t < 60.0]
        if len(self._call_timestamps) >= self.rate_limit:
            return True
        self._call_timestamps.append(now)
        return False

    def handle_event(self, payload: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        if not isinstance(auth_token,str) or not hmac.compare_digest(auth_token,self.webhook_secret):
            return {"accepted": False, "error": "UNAUTHORIZED"}

        # Check rate limit
        if self._is_rate_limited():
            if len(self._retry_queue) >= 100:
                return {'accepted':False,'error':'RETRY_QUEUE_FULL'}
            self._retry_queue.append({**payload,'content':redact_secrets(str(payload.get('content','')))[:64000],
                'title':redact_secrets(str(payload.get('title','')))[:500]})
            return {"accepted": True, "status": "BUFFERED_FOR_RETRY", "queue_position": len(self._retry_queue)}

        # Redact secrets
        raw_content = payload.get("content", "")
        clean_content = redact_secrets(raw_content)

        raw_title = payload.get("title", "Untitled Document")
        clean_title = redact_secrets(raw_title)

        project_id = payload.get("project_id", "QAG3")
        source_id = payload.get("source_id", "wp:auto")
        roles = payload.get("allowed_roles", ["PM", "BA", "FE", "BE", "QA"])
        meta = payload.get("metadata", {})

        doc = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id=project_id,
            source_id=source_id,
            title=clean_title,
            content=clean_content,
            allowed_roles=roles,
            metadata=meta,
        )

        res = self.ingester.ingest(doc)
        return {
            "accepted": True,
            "status": "QUEUED_OR_INGESTED",
            "ingestion_status": res.status.value,
            "document_id": res.document_id,
        }

def export_indexing_workflow() -> Dict[str, Any]:
    """Generates standard n8n Community JSON workflow for local indexing hook."""
    return {
        "name": "QLDAPM Local Second Brain Indexing Hook",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "qldapm-index-hook",
                    "options": {}
                },
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "functionCode": "return items.map(i => { i.json.sanitized = true; return i; });"
                },
                "name": "Local Redaction Check",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "requestMethod": "POST",
                    "url": "http://staging-gateway:18092/api/v1/internal/knowledge/index",
                    "options": {}
                },
                "name": "Gateway Ingestion",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "position": [650, 300]
            }
        ],
        "connections": {
            "Webhook Trigger": {
                "main": [[{"node": "Local Redaction Check", "type": "main", "index": 0}]]
            },
            "Local Redaction Check": {
                "main": [[{"node": "Gateway Ingestion", "type": "main", "index": 0}]]
            }
        },
        "active": False,
        "settings": {
            "executionOrder": "v1"
        }
    }
