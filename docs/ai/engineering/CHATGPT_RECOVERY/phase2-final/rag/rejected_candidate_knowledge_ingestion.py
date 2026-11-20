"""Idempotent Ingestion, Section-Aware Chunking and Dense Vector Pipeline for QLDAPM Local Second Brain.
Enforces deduplication, revision hashing, ACL metadata propagation, and Qdrant + SQLite synchronization.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional
from .knowledge_classifier import KnowledgeDocument
from .knowledge_storage import KnowledgeStorage
from .vector_client import VectorClient
from .knowledge_lock import lease
from .knowledge_points import point as vector_point,remember,prune
from contextlib import nullcontext

logger = logging.getLogger("qldapm.knowledge_ingestion")


class IngestionStatus(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SKIPPED_UNCHANGED = "SKIPPED_UNCHANGED"
    FAILED = "FAILED"


@dataclass
class IngestionResult:
    status: IngestionStatus
    document_id: str
    source_id: str
    chunks_count: int
    source_hash: str
    vector_indexed: bool = False
    error: Optional[str] = None


def chunk_text(text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
    """Deterministic, section-aware and bounded sliding window chunking."""
    if type(chunk_size) is not int or type(chunk_overlap) is not int or not 0 <= chunk_overlap < chunk_size <= 10000:
        raise ValueError('KNOWLEDGE_CHUNK_BOUNDS_INVALID')
    cleaned = text.strip()
    if not cleaned:
        return []

    # If already shorter than chunk_size, single chunk
    if len(cleaned) <= chunk_size:
        hasher = hashlib.sha256()
        hasher.update(f"0:{cleaned}".encode("utf-8"))
        return [{
            "chunk_index": 0,
            "chunk_text": cleaned,
            "chunk_hash": hasher.hexdigest(),
        }]

    step = max(1, chunk_size - chunk_overlap)
    chunks: List[Dict[str, Any]] = []
    start = 0
    idx = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk_str = cleaned[start:end].strip()
        if chunk_str:
            hasher = hashlib.sha256()
            hasher.update(f"{idx}:{chunk_str}".encode("utf-8"))
            chunks.append({
                "chunk_index": idx,
                "chunk_text": chunk_str,
                "chunk_hash": hasher.hexdigest(),
            })
            idx += 1
        if end >= len(cleaned):
            break
        start += step

    # Audit JSON can bury a complete requirement between hashes; retain its literal passage too.
    seen = {c['chunk_text'] for c in chunks}
    passages = list(cleaned.splitlines()) + [m.group(1) for m in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned)]
    for passage in passages:
        passage = passage.strip()
        # shortcut: short generic fragments lose context; reassess with an adjudicated corpus/reranker.
        if not 60 <= len(passage) <= chunk_size or not any(c.isspace() for c in passage) or passage in seen:
            continue
        index = len(chunks)
        chunks.append({'chunk_index': index, 'chunk_text': passage,
            'chunk_hash': hashlib.sha256(f'{index}:{passage}'.encode('utf-8')).hexdigest()})
        seen.add(passage)
    return chunks


class KnowledgeIngester:
    def __init__(
        self,
        storage: KnowledgeStorage,
        vector_client: Optional[VectorClient] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ):
        self.storage = storage
        self.vector_client = vector_client
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._chunks_store: Dict[str, List[Dict[str, Any]]] = {}

    def count_chunks(self, document_id: str) -> int:
        if self.storage.db_path != ':memory:':
            with self.storage._connection() as db:
                return db.execute('SELECT count(*) FROM knowledge_chunks WHERE document_id=?', (document_id,)).fetchone()[0]
        return len(self._chunks_store.get(document_id, []))

    def ingest(self, doc: KnowledgeDocument) -> IngestionResult:
        guard = lease(self.storage.db_path + '.ingest.lock') if self.storage.db_path != ':memory:' else nullcontext()
        with guard:
            return self._ingest(doc)

    def _ingest(self, doc: KnowledgeDocument) -> IngestionResult:
        self.storage._reload()
        existing = self.storage._mock_tables.get(f"{self.storage.schema_name}.knowledge_documents", {})
        old = existing.get(doc.source_hash)
        unchanged = bool(old and all(old.get(k) == v for k,v in {
            'title':doc.title, 'allowed_roles':doc.allowed_roles, 'metadata':doc.metadata}.items()))
        previous = next((h for h,d in existing.items() if
            (d.get('source_id'),d.get('project_id'),d.get('doc_type')) ==
            (doc.source_id,doc.project_id,doc.doc_type.value)),None)
        chunks = chunk_text(doc.content,self.chunk_size,self.chunk_overlap)
        points = []
        if self.vector_client and self.vector_client.enabled:
            for chunk in chunks:
                points.append(vector_point(doc,chunk,self.vector_client))
        vector_enabled = bool(self.vector_client and self.vector_client.enabled)
        plan=remember(self.storage,self.vector_client,doc) if vector_enabled else []
        if unchanged and (not vector_enabled or self.vector_client.verify_points(points)):
            if vector_enabled:
                try:prune(self.storage,self.vector_client,doc,plan,[p['id'] for p in points])
                except Exception:
                    return IngestionResult(IngestionStatus.FAILED,doc.source_hash,doc.source_id,len(chunks),doc.source_hash,False,'VECTOR_INDEX_PENDING')
            return IngestionResult(IngestionStatus.SKIPPED_UNCHANGED,doc.source_hash,doc.source_id,
                len(chunks),doc.source_hash,vector_enabled)
        if not self.storage.store_document(doc,chunks=chunks):
            return IngestionResult(IngestionStatus.FAILED,doc.source_hash,doc.source_id,0,doc.source_hash,False,'PERSISTENCE_FAILED')
        if previous and previous != doc.source_hash and self.storage.db_path == ':memory:':
            self.storage.delete_document(previous)
            self._chunks_store.pop(previous,None)
        self._chunks_store[doc.source_hash]=chunks
        vector_ok=False
        if vector_enabled:
            try:
                embeddings=self.vector_client.embed_texts([c['chunk_text'] for c in chunks])
                if len(embeddings)!=len(points):raise ValueError('EMBEDDING_COUNT_MISMATCH')
                for point,embedding in zip(points,embeddings):point['vector']=embedding
                if self.vector_client.upsert_points(points) and self.vector_client.verify_points(points):
                    prune(self.storage,self.vector_client,doc,plan,[p['id'] for p in points])
                    vector_ok=True
            except Exception as error:
                logger.warning('Vector indexing pending: %s',type(error).__name__)
            if not vector_ok:
                # SQLite is the durable retry input; unchanged content must attempt vector repair next time.
                return IngestionResult(IngestionStatus.FAILED,doc.source_hash,doc.source_id,len(chunks),
                    doc.source_hash,False,'VECTOR_INDEX_PENDING')
        return IngestionResult(IngestionStatus.UPDATED if previous else IngestionStatus.CREATED,
            doc.source_hash,doc.source_id,len(chunks),doc.source_hash,vector_ok)

    def deindex_source(self, source_id: str, project_id: str | None = None) -> bool:
        guard = lease(self.storage.db_path + '.ingest.lock') if self.storage.db_path != ':memory:' else nullcontext()
        with guard:
            return self._deindex_source(source_id,project_id)

    def _deindex_source(self, source_id: str, project_id: str | None = None) -> bool:
        """Deindex and purge all documents and chunks associated with a source_id from SQLite and Qdrant."""
        tbl_doc = f"{self.storage.schema_name}.knowledge_documents"
        self.storage._reload()
        existing_docs = self.storage._mock_tables.get(tbl_doc, {})

        matches = [h for h, d in existing_docs.items() if d.get('source_id') == source_id and (project_id is None or d.get('project_id') == project_id)]
        if len(matches) > 1:
            raise ValueError('KNOWLEDGE_SOURCE_SCOPE_REQUIRED')

        target_hash = None
        for h, d in list(existing_docs.items()):
            if d.get("source_id") == source_id and (project_id is None or d.get('project_id') == project_id):
                target_hash = h
                break

        if not target_hash:
            return False

        if self.vector_client and self.vector_client.enabled:
            doc=next(d for d in self.storage.query_documents(existing_docs[target_hash]['project_id']) if d.source_hash==target_hash)
            try:
                plan=remember(self.storage,self.vector_client,doc)
                prune(self.storage,self.vector_client,doc,plan,[])
            except Exception:return False
        deleted = self.storage.delete_document(target_hash)
        if deleted:
            self._chunks_store.pop(target_hash,None)
        return deleted
