"""Conversation Memory with TTL and Exact Object References for QLDAPM.
Isolates memory per (actor_id, project_id, conversation_id) and refreshes on lock_version changes.
"""
from dataclasses import dataclass
import re
import time
from typing import Dict, Optional, Tuple

PRONOUN_PATTERN = re.compile(
    r"(?:task|work\s*package|ticket|yêu\s*cầu|cái|nó)\s+(?:đó|này|vừa\s*rồi|kia)|(?:cái\s+này|cái\s+đó)|(?:that|this)\s+(?:task|ticket|work\s*package|item|bug|issue)",
    re.IGNORECASE,
)

@dataclass
class NativeObjectRef:
    native_type: str
    native_id: int
    lock_version: int

@dataclass
class MemoryEntry:
    obj_ref: NativeObjectRef
    updated_at: float
    expires_at: float

class ConversationMemory:
    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        # Key: (actor_id, project_id, conversation_id)
        self._store: Dict[Tuple[int, str, str], MemoryEntry] = {}

    def _key(self, actor_id: int, project_id: str, conversation_id: str) -> Tuple[int, str, str]:
        return (actor_id, project_id.strip().upper(), conversation_id.strip())

    def set_object_ref(
        self,
        actor_id: int,
        project_id: str,
        conversation_id: str,
        obj_ref: NativeObjectRef,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        key = self._key(actor_id, project_id, conversation_id)
        self._store[key] = MemoryEntry(
            obj_ref=obj_ref,
            updated_at=now,
            expires_at=now + ttl,
        )

    def get_last_object_ref(
        self,
        actor_id: int,
        project_id: str,
        conversation_id: str,
    ) -> Optional[NativeObjectRef]:
        key = self._key(actor_id, project_id, conversation_id)
        entry = self._store.get(key)
        if not entry:
            return None

        # Check TTL
        if time.time() > entry.expires_at:
            del self._store[key]
            return None

        return entry.obj_ref

    def refresh_object_version(
        self,
        actor_id: int,
        project_id: str,
        conversation_id: str,
        native_id: int,
        new_lock_version: int,
    ) -> bool:
        ref = self.get_last_object_ref(actor_id, project_id, conversation_id)
        if ref and ref.native_id == native_id:
            ref.lock_version = new_lock_version
            now = time.time()
            key = self._key(actor_id, project_id, conversation_id)
            self._store[key].updated_at = now
            self._store[key].expires_at = now + self.default_ttl
            return True
        return False

    def resolve_reference(
        self,
        text: str,
        actor_id: int,
        project_id: str,
        conversation_id: str,
    ) -> Optional[NativeObjectRef]:
        """Resolves relative pronouns ('task đó', 'cái đó') to exact stored object reference."""
        if not PRONOUN_PATTERN.search(text):
            return None
        return self.get_last_object_ref(actor_id, project_id, conversation_id)

    def clear_conversation(
        self,
        actor_id: int,
        project_id: str,
        conversation_id: str,
    ) -> None:
        key = self._key(actor_id, project_id, conversation_id)
        if key in self._store:
            del self._store[key]
