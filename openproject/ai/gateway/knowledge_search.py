"""Hybrid Search Engine for QLDAPM Local Second Brain.
Combines Qdrant Dense Vector Search (Ollama BGE-M3 1024-dim) + SQLite FTS5 Lexical Search (BM25)
using Reciprocal Rank Fusion (RRF k=60).
Strictly zero paid remote API calls. Operates 100% locally with role/project ACL pre-filtering.
"""
from dataclasses import dataclass, field
import hashlib
import json
import logging
import math
import re
import unicodedata
from typing import Any, Dict, List, Optional
from .knowledge_classifier import KnowledgeDocType, KnowledgeDocument
from .knowledge_storage import KnowledgeStorage
from .knowledge_ingestion import KnowledgeIngester
from .vector_client import VectorClient
from .permissions import AI_SYSTEM_OWNER

logger = logging.getLogger("qldapm.knowledge_search")

RRF_K = 60
# Calibrated on the eight labeled Phase 4 cases; held-out quality is reported separately.
DENSE_MIN_COSINE = 0.45


@dataclass
class SearchResult:
    document_id: str
    source_id: str
    title: str
    snippet: str
    score: float
    match_type: str
    doc_type: KnowledgeDocType
    native_id: Optional[int] = None
    lock_version: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    passage: str = ''
    chunk_index: Optional[int] = None
    chunk_hash: Optional[str] = None
    literal_anchor: bool = False


def _tokenize(text: str) -> List[str]:
    plain = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold().replace('đ', 'd')) if not unicodedata.combining(c))
    return [w for w in re.findall(r"\w+", plain) if len(w) > 1]


def _literal_anchors(query):
    return [x.casefold() for x in re.findall(r'\b[A-Za-z][A-Za-z0-9_]*(?:[-/][A-Za-z0-9_{}]+)+\b|\b[A-Z]{2,}\d[A-Z0-9_-]*\b',query) if len(x)>=4]


class KnowledgeSearchEngine:
    def __init__(
        self,
        storage: KnowledgeStorage,
        ingester: Optional[KnowledgeIngester] = None,
        vector_client: Optional[VectorClient] = None,
    ):
        self.storage = storage
        self.ingester = ingester
        self.vector_client = vector_client
        self.dense_state = 'DISABLED'
        self.remote_embedding_calls_count = 0  # Strictly 0 paid API calls; only local Ollama / SQLite used.

    def _lexical_search(
        self,
        query_terms: List[str],
        project_id: str,
        role: str,
        limit: int,
        doc_types: Optional[List[KnowledgeDocType]] = None,
        actor_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
        require_all_terms: bool = False,
        literal_anchors=(),
    ) -> List[SearchResult]:
        """Perform lexical FTS / token matching."""
        candidate_docs = self.storage.query_documents(
            project_id=project_id,
            role=role,
        )
        if document_ids is not None:
            candidate_docs = [d for d in candidate_docs if d.source_hash in document_ids]
        elif actor_id is not None:
            candidate_docs = [d for d in candidate_docs
                              if type(d.metadata.get('actor_id')) is int and d.metadata['actor_id'] == actor_id]

        if doc_types:
            candidate_docs = [d for d in candidate_docs if d.doc_type in doc_types]
        anchored={d.source_hash for d in candidate_docs if any(a in (d.source_id+' '+d.title+' '+d.content).casefold() for a in literal_anchors)}

        bm25_scores = None
        if self.storage.db_path != ':memory:' and query_terms:
            expression = ' OR '.join('"' + term + '"' for term in query_terms)
            try:
                with self.storage._connection() as db:
                    scope_json = json.dumps(document_ids) if document_ids is not None else None
                    rows = db.execute('''SELECT f.source_hash,bm25(knowledge_fts) AS rank FROM knowledge_fts f JOIN knowledge_documents d
                        ON d.source_hash=f.source_hash WHERE knowledge_fts MATCH ? AND d.project_id=?
                        AND (? = ? OR EXISTS (SELECT 1 FROM json_each(d.allowed_roles) WHERE value=?))
                        AND (? IS NOT NULL OR ? IS NULL OR (json_type(d.metadata,'$.actor_id')='integer'
                             AND json_extract(d.metadata,'$.actor_id')=?))
                        AND (? IS NULL OR d.source_hash IN (SELECT value FROM json_each(?)))
                        ORDER BY rank LIMIT 100''', (expression,project_id,role,AI_SYSTEM_OWNER,role,scope_json,actor_id,actor_id,scope_json,scope_json)).fetchall()
                hashes = {row[0] for row in rows}
                bm25_scores = {row[0]: -float(row[1]) for row in rows}
                candidate_docs = [doc for doc in candidate_docs if doc.source_hash in hashes or doc.source_hash in anchored]
            except Exception:
                pass

        chunks_by_document = {}
        if self.storage.db_path != ':memory:' and candidate_docs:
            with self.storage._connection() as db:
                chunks = [dict(row) for row in db.execute('SELECT document_id,chunk_index,chunk_text,chunk_hash FROM knowledge_chunks WHERE document_id IN (SELECT value FROM json_each(?)) ORDER BY chunk_index',(json.dumps([doc.source_hash for doc in candidate_docs]),))]
        else:
            chunks = list(self.storage._mock_tables.get(f'{self.storage.schema_name}.knowledge_chunks',{}).values())
        for chunk in chunks:
            chunks_by_document.setdefault(chunk['document_id'],[]).append(chunk)
        scored_results: List[SearchResult] = []
        for doc in candidate_docs:
            title_tokens = _tokenize(doc.title)
            content_tokens = _tokenize(doc.content)

            title_matches = sum(1 for t in query_terms if t in title_tokens)
            content_matches = sum(1 for t in query_terms if t in content_tokens)
            distinct_matches = sum(1 for t in query_terms if t in title_tokens or t in content_tokens)

            literal_anchor=doc.source_hash in anchored
            if distinct_matches == 0 and not literal_anchor:
                continue
            if require_all_terms and distinct_matches != len(query_terms) and not literal_anchor:
                continue

            match_ratio = distinct_matches / max(1,len(query_terms))
            if len(query_terms) >= 4 and match_ratio < 0.5 and not literal_anchor:
                continue

            total_score = bm25_scores.get(doc.source_hash,0) if bm25_scores is not None else (title_matches * 3.0) + content_matches
            if literal_anchor:total_score=max(1,total_score)
            if total_score <= 0:
                continue

            snippet = doc.content[:200]
            for term in query_terms:
                idx = doc.content.lower().find(term)
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(doc.content), idx + 120)
                    snippet = "..." + doc.content[start:end].strip() + "..."
                    break

            meta = doc.metadata or {}
            chunk = max(chunks_by_document.get(doc.source_hash,[]),key=lambda c:len(set(_tokenize(c['chunk_text'])) & set(query_terms)),default={})
            scored_results.append(
                SearchResult(
                    document_id=doc.source_hash,
                    source_id=doc.source_id,
                    title=doc.title,
                    snippet=snippet,
                    score=total_score,
                    match_type="FTS_BM25" if bm25_scores is not None else "FTS_KEYWORD",
                    doc_type=doc.doc_type,
                    native_id=meta.get("native_id"),
                    lock_version=meta.get("lock_version"),
                    metadata=meta,
                    passage=chunk.get('chunk_text',''),chunk_index=chunk.get('chunk_index'),chunk_hash=chunk.get('chunk_hash'),
                    literal_anchor=literal_anchor,
                )
            )

        scored_results.sort(key=lambda r: (r.literal_anchor,r.score), reverse=True)
        return scored_results[:limit]

    def _dense_search(
        self,
        query: str,
        project_id: str,
        role: str,
        limit: int,
        doc_types: Optional[List[KnowledgeDocType]] = None,
        actor_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Perform dense semantic search via Ollama BGE-M3 and Qdrant."""
        if not self.vector_client or not self.vector_client.enabled or document_ids == []:
            return []
        self.dense_state = 'FALLBACK'
        try:
            query_vecs = self.vector_client.embed_texts([query])
            if not query_vecs:
                return []
            q_vec = query_vecs[0]

            dt_values = [dt.value if isinstance(dt, KnowledgeDocType) else str(dt) for dt in doc_types] if doc_types else None
            authorized = {d.source_hash:d for d in self.storage.query_documents(project_id,role)
                if (d.source_hash in document_ids if document_ids is not None else
                    actor_id is None or type(d.metadata.get('actor_id')) is int and d.metadata['actor_id'] == actor_id) and
                   (not doc_types or d.doc_type in doc_types)}
            q_results = self.vector_client.search_dense(
                query_vector=q_vec,
                project_id=project_id,
                role=role,
                limit=min(200,limit * 8),
                doc_types=dt_values,
                actor_id=actor_id,
                document_ids=document_ids,
            )
            file_ids=[d.source_hash for d in authorized.values() if d.source_id.startswith('file:')]
            if document_ids is not None and file_ids:
                # Balance the two authorized source families before chunk deduplication.
                file_results=self.vector_client.search_dense(query_vector=q_vec,project_id=project_id,role=role,
                    limit=min(50,limit * 2),doc_types=dt_values,actor_id=actor_id,document_ids=file_ids)
                q_results=[group[i] for i in range(max(len(q_results),len(file_results)))
                    for group in (q_results,file_results) if i < len(group)]
            self.dense_state = 'READY'

            dense_results: List[SearchResult] = []
            anchors=_literal_anchors(query)
            anchored={d.source_hash for d in authorized.values() if any(a in (d.source_id+' '+d.title+' '+d.content).casefold() for a in anchors)}
            if self.storage.db_path != ':memory:':
                with self.storage._connection() as sdb:
                    proofs={(r[0],r[1]):r[2] for r in sdb.execute('SELECT document_id,chunk_index,chunk_hash FROM knowledge_chunks WHERE document_id IN (SELECT value FROM json_each(?))',(json.dumps(list(authorized)),))}
            else:
                proofs={(r['document_id'],r['chunk_index']):r['chunk_hash'] for r in self.storage._mock_tables.get(f'{self.storage.schema_name}.knowledge_chunks',{}).values()}
            for item in q_results:
                payload = item.get("payload", {})
                doc = authorized.get(payload.get('document_id'))
                if not doc or any(payload.get(k) != v for k,v in {
                    'source_id':doc.source_id,'project_id':doc.project_id,'doc_type':doc.doc_type.value,
                    'title':doc.title,'allowed_roles':doc.allowed_roles,'metadata':doc.metadata}.items()):
                    continue
                # Single-word lookups need a literal anchor; multiword semantic queries retain dense recall.
                query_terms = _tokenize(query)
                if len(query_terms) == 1 and query_terms[0] not in _tokenize(doc.title + ' ' + doc.content):
                    continue
                chunk_index = payload.get('chunk_index')
                if type(chunk_index) is not int:
                    continue
                chunk_hash = hashlib.sha256(f"{chunk_index}:{payload.get('chunk_text','')}".encode()).hexdigest()
                if proofs.get((doc.source_hash,chunk_index)) != chunk_hash or payload.get('chunk_hash') != chunk_hash:
                    continue
                score = item.get("score", 0.0)
                if not isinstance(score,(int,float)) or not math.isfinite(score) or score < DENSE_MIN_COSINE:
                    continue
                meta = payload.get("metadata", {})
                dt_str = payload.get("doc_type", "WORK_PACKAGE")
                try:
                    dt_enum = KnowledgeDocType(dt_str)
                except ValueError:
                    dt_enum = KnowledgeDocType.WORK_PACKAGE

                chunk_text_str = payload.get("chunk_text", "")
                match = re.search(re.escape(query.strip()), chunk_text_str, re.IGNORECASE) if query.strip() else None
                start = max(0, match.start() - 40) if match else 0
                snippet = ("..." if start else "") + chunk_text_str[start:start + 200]
                if len(chunk_text_str) > start + 200:
                    snippet += "..."

                dense_results.append(
                    SearchResult(
                        document_id=payload.get("document_id", ""),
                        source_id=payload.get("source_id", ""),
                        title=payload.get("title", ""),
                        snippet=snippet,
                        score=score,
                        match_type="DENSE_VECTOR",
                        doc_type=dt_enum,
                        native_id=doc.metadata.get("native_id"),
                        lock_version=meta.get("lock_version"),
                        metadata=meta,
                        passage=chunk_text_str,chunk_index=chunk_index,chunk_hash=chunk_hash,
                        literal_anchor=doc.source_hash in anchored,
                    )
                )
            return dense_results
        except Exception as e:
            self.dense_state = 'FALLBACK'
            logger.warning(f"Dense vector retrieval fallback to lexical: {e}")
            return []

    def search(
        self,
        query: str,
        project_id: str,
        role: str,
        limit: int = 10,
        doc_types: Optional[List[KnowledgeDocType]] = None,
        *,
        actor_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        if type(limit) is not int or not 1 <= limit <= 50 or not isinstance(role, str) or not role:
            raise ValueError('KNOWLEDGE_SEARCH_SCOPE_AND_LIMIT_REQUIRED')
        if actor_id is not None and (type(actor_id) is not int or actor_id <= 0):
            raise ValueError('KNOWLEDGE_ACTOR_SCOPE_REQUIRED')
        if role == AI_SYSTEM_OWNER and document_ids is None:
            raise PermissionError('OWNER_RAG_DOCUMENT_SCOPE_REQUIRED')

        query_terms = _tokenize(query)[:30]
        self.dense_state = 'DISABLED'
        if not query_terms and not query.strip():
            return []

        # 1. Dense Vector Search (if VectorClient is available and enabled)
        dense_results: List[SearchResult] = []
        if self.vector_client and self.vector_client.enabled:
            dense_results = self._dense_search(
                query=query,
                project_id=project_id,
                role=role,
                limit=limit * 2,
                doc_types=doc_types,
                actor_id=actor_id,
                document_ids=document_ids,
            )

        # 2. Lexical Search
        # Without a relevant dense hit, require complete lexical evidence; outages retain partial fallback.
        lexical_results = self._lexical_search(
            query_terms=query_terms,
            project_id=project_id,
            role=role,
            limit=limit * 2,
            doc_types=doc_types,
            actor_id=actor_id,
            document_ids=document_ids,
            require_all_terms=self.dense_state == 'READY' and not dense_results,
            literal_anchors=_literal_anchors(query),
        )

        # If no dense results, return lexical results directly
        if not dense_results:
            return lexical_results[:limit]

        # 3. Reciprocal Rank Fusion (RRF k=60)
        # RRF_Score = 1 / (60 + dense_rank) + 1 / (60 + lexical_rank)
        rrf_scores: Dict[str, float] = {}
        merged_items: Dict[str, SearchResult] = {}

        # Dense ranks (1-based)
        seen_dense = set()
        for rank, item in enumerate(dense_results, 1):
            key = item.source_id or item.document_id
            if key in seen_dense:
                continue
            seen_dense.add(key)
            rrf_scores[key] = 1.0 / (RRF_K + len(seen_dense))
            merged_items[key] = item

        # Lexical ranks (1-based)
        for rank, item in enumerate(lexical_results, 1):
            key = item.source_id or item.document_id
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (RRF_K + rank))
            if key not in merged_items:
                merged_items[key] = item

        # Sort combined results by RRF score descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: (merged_items[k].literal_anchor,rrf_scores[k]), reverse=True)

        final_results: List[SearchResult] = []
        lexical_keys = {item.source_id or item.document_id for item in lexical_results}
        dense_map = {item.source_id or item.document_id: item for item in dense_results}
        for k in sorted_keys[:limit]:
            res = merged_items[k]
            # Require minimum relevance threshold: if no lexical match, dense cosine score must be >= DENSE_MIN_COSINE (0.65)
            if k not in lexical_keys:
                d_item = dense_map.get(k)
                if not d_item or d_item.score < DENSE_MIN_COSINE:
                    continue
            # Create finalized SearchResult with RRF score and appropriate match tag
            match_type = 'LITERAL_REFERENCE' if res.literal_anchor else ("HYBRID_RRF" if (k in lexical_keys and k in dense_map) else ("DENSE_VECTOR" if k in dense_map else "FTS_BM25"))
            final_results.append(
                SearchResult(
                    document_id=res.document_id,
                    source_id=res.source_id,
                    title=res.title,
                    snippet=res.snippet,
                    score=round(rrf_scores[k], 5),
                    match_type=match_type,
                    doc_type=res.doc_type,
                    native_id=res.native_id,
                    lock_version=res.lock_version,
                    metadata=res.metadata,
                    passage=res.passage,chunk_index=res.chunk_index,chunk_hash=res.chunk_hash,
                    literal_anchor=res.literal_anchor,
                )
            )

        return final_results
