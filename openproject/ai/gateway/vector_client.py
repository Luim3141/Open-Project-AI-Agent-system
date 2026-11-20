"""Vector Client for QLDAPM Local Second Brain RAG.
Interacts with local Ollama BGE-M3 for 1024-dim dense embeddings
and local Qdrant Vector Database for dense similarity search and persistence.
Adheres strictly to hardware bounds (batch size = 2, 1 worker, 1024 dims).
"""
import hashlib
import json
import logging
import math
import os
import time
import uuid
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from .engineering_fencing import ensure_current
from .knowledge_lock import lease

logger = logging.getLogger("qldapm.vector_client")

COLLECTION_NAME = "qldapm_knowledge_dense"
EMBEDDING_MODEL = "bge-m3"
EMBEDDING_DIM = 1024
DEFAULT_BATCH_SIZE = 2


def _resolve_url(env_var: str, default_host_url: str, default_docker_url: str) -> str:
    explicit = os.environ.get(env_var)
    if explicit:
        return explicit.rstrip("/")
    # Detect if running inside Docker container
    if os.path.exists("/.dockerenv"):
        return default_docker_url.rstrip("/")
    return default_host_url.rstrip("/")


class VectorClient:
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        collection_name: str = COLLECTION_NAME,
        batch_size: int = DEFAULT_BATCH_SIZE,
        enabled: bool = True,
        timeout: float = 60.0,
    ):
        self.ollama_url = (ollama_url or _resolve_url(
            "QLDAPM_OLLAMA_URL",
            "http://127.0.0.1:11434",
            "http://host.docker.internal:11434",
        )).rstrip("/")
        self.qdrant_url = (qdrant_url or _resolve_url(
            "QLDAPM_QDRANT_URL",
            "http://127.0.0.1:6333",
            "http://qldapm-qdrant:6333",
        )).rstrip("/")
        self.collection_name = collection_name
        self.batch_size = max(1, min(batch_size, 2))
        self.enabled = enabled
        self.timeout = timeout
        self._http = httpx.Client(timeout=timeout)

    def close(self):
        self._http.close()

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            r_ol = self._http.get(f"{self.ollama_url}/api/tags", timeout=3.0)
            r_qd = self._http.get(f"{self.qdrant_url}/collections", timeout=3.0)
            return r_ol.status_code == 200 and r_qd.status_code == 200
        except Exception:
            return False

    def ensure_collection(self) -> bool:
        if not self.enabled:
            return False
        try:
            r = self._http.get(f"{self.qdrant_url}/collections/{self.collection_name}", timeout=5.0)
            if r.status_code == 200:
                vectors = r.json()['result']['config']['params']['vectors']
                return vectors.get('size') == EMBEDDING_DIM and vectors.get('distance') == 'Cosine'
            if r.status_code != 404:
                return False
            # Create collection with 1024 dims and Cosine distance
            body = {
                "vectors": {
                    "size": EMBEDDING_DIM,
                    "distance": "Cosine",
                },
                "hnsw_config": {
                    "m": 16,
                    "ef_construct": 100,
                },
            }
            ensure_current()
            r_create = self._http.put(f"{self.qdrant_url}/collections/{self.collection_name}", json=body, timeout=10.0)
            return r_create.status_code in (200, 201)
        except Exception as e:
            logger.warning(f"Qdrant ensure_collection error: {e}")
            return False

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        root = Path(os.environ.get('QLDAPM_AI_RUNTIME') or tempfile.gettempdir())
        with lease(root / 'qldapm-bge-m3.lock'):
            return self._embed_texts(texts)

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings for a list of texts in small bounded batches."""
        if not self.enabled or not texts:
            return []

        all_embeddings: List[List[float]] = []
        deadline=time.monotonic()+90

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            payload = {
                "model": EMBEDDING_MODEL,
                "input": batch,
                "truncate": False,
            }
            try:
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    raise TimeoutError('EMBEDDING_TOTAL_DEADLINE_EXCEEDED')
                res = self._http.post(f"{self.ollama_url}/api/embed", json=payload, timeout=min(self.timeout,remaining))
                if res.status_code != 200:
                    raise RuntimeError(f"Ollama embedding error HTTP {res.status_code}: {res.text[:200]}")
                data = res.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) != len(batch):
                    raise ValueError(f"Ollama returned {len(embeddings)} vectors for {len(batch)} inputs")

                for vec in embeddings:
                    if len(vec) != EMBEDDING_DIM:
                        raise ValueError(f"Vector dim {len(vec)} != expected {EMBEDDING_DIM}")
                    if any(math.isnan(x) or math.isinf(x) for x in vec):
                        raise ValueError("Vector contains NaN or Inf values")
                    all_embeddings.append(vec)
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise

        return all_embeddings

    def deterministic_uuid(self, chunk_id: str) -> str:
        """Create a stable UUID from a chunk identifier string."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"qldapm.chunk.{chunk_id}"))

    def upsert_points(self, points: List[Dict[str, Any]]) -> bool:
        if not self.enabled or not points:
            return True
        try:
            if not self.ensure_collection():
                return False
            url = f"{self.qdrant_url}/collections/{self.collection_name}/points"
            ensure_current()
            res = self._http.put(url, params={'wait': 'true'}, json={"points": points}, timeout=self.timeout)
            return res.status_code == 200 and res.json().get('result', {}).get('status') == 'completed'
        except Exception as e:
            logger.error(f"Qdrant upsert error: {e}")
            return False

    def delete_by_source_id(self, source_id: str, project_id: Optional[str] = None) -> bool:
        """Delete all vector points associated with a source_id from Qdrant."""
        if not self.enabled:
            return True
        try:
            must_filters: List[Dict[str, Any]] = [
                {"key": "source_id", "match": {"value": str(source_id)}}
            ]
            if project_id is not None:
                must_filters.append({"key": "project_id", "match": {"value": str(project_id)}})

            body = {
                "filter": {
                    "must": must_filters
                }
            }
            url = f"{self.qdrant_url}/collections/{self.collection_name}/points/delete"
            ensure_current()
            res = self._http.post(url, params={'wait': 'true'}, json=body, timeout=10.0)
            if res.status_code != 200 or res.json().get('result', {}).get('status') != 'completed':
                return False
            readback = self._http.post(f"{self.qdrant_url}/collections/{self.collection_name}/points/scroll",
                json={**body, 'limit': 1, 'with_payload': False, 'with_vector': False}, timeout=10.0)
            return readback.status_code == 200 and readback.json()['result']['points'] == []
        except Exception as e:
            logger.error(f"Qdrant delete error for source_id {source_id}: {e}")
            return False

    def verify_points(self, points: List[Dict[str, Any]]) -> bool:
        """Read back exact point identity and payload; HTTP success alone is not indexing proof."""
        try:
            for start in range(0, len(points), 100):
                batch = points[start:start + 100]
                response = self._http.post(f"{self.qdrant_url}/collections/{self.collection_name}/points",
                    json={'ids': [p['id'] for p in batch], 'with_payload': True, 'with_vector': False}, timeout=10.0)
                if response.status_code != 200:
                    return False
                actual = {str(p['id']): p.get('payload', {}) for p in response.json()['result']}
                if len(actual) != len(batch) or any(actual.get(p['id']) != p['payload'] for p in batch):
                    return False
            return True
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return False

    def delete_verified_points(self, points: List[Dict[str, Any]]) -> None:
        """Delete only persisted, registered point identities after checking every existing payload."""
        if len(points)>10000 or len({p['id'] for p in points})!=len(points):
            raise ValueError('KNOWLEDGE_DELETE_SCOPE_INVALID')
        def read(batch):
            response=self._http.post(f'{self.qdrant_url}/collections/{self.collection_name}/points',
                json={'ids':[p['id'] for p in batch],'with_payload':True,'with_vector':False},timeout=10)
            response.raise_for_status()
            return {str(p['id']):p.get('payload',{}) for p in response.json()['result']}
        for start in range(0,len(points),100):
            batch=points[start:start+100];actual=read(batch)
            if set(actual)-{p['id'] for p in batch} or any(p['id'] in actual and actual[p['id']]!=p['payload'] for p in batch):
                raise ValueError('KNOWLEDGE_DELETE_PAYLOAD_MISMATCH_HOLD')
        for start in range(0,len(points),100):
            batch=points[start:start+100]
            ensure_current()
            response=self._http.post(f'{self.qdrant_url}/collections/{self.collection_name}/points/delete?wait=true',
                json={'points':[p['id'] for p in batch]},timeout=10)
            response.raise_for_status()
            if read(batch):raise ValueError('KNOWLEDGE_DELETE_READBACK_FAILED')

    def delete_registered_points(self, candidates, keep_ids):
        """Every historical payload variant comes from a persisted registration, never a source filter."""
        if len(candidates)>10000:raise ValueError('KNOWLEDGE_DELETE_SCOPE_INVALID')
        allowed={};keep_ids=set(keep_ids)
        for point in candidates:
            if point['id'] not in keep_ids:allowed.setdefault(point['id'],[]).append(point['payload'])
        if len(allowed)>10000:raise ValueError('KNOWLEDGE_DELETE_SCOPE_INVALID')
        targets=[];identifiers=list(allowed)
        for start in range(0,len(identifiers),100):
            ids=identifiers[start:start+100]
            response=self._http.post(f'{self.qdrant_url}/collections/{self.collection_name}/points',
                json={'ids':ids,'with_payload':True,'with_vector':False},timeout=10)
            response.raise_for_status();actual={str(p['id']):p.get('payload',{}) for p in response.json()['result']}
            if set(actual)-set(ids) or any(payload not in allowed[identifier] for identifier,payload in actual.items()):
                raise ValueError('KNOWLEDGE_DELETE_PAYLOAD_MISMATCH_HOLD')
            targets.extend({'id':identifier,'payload':actual.get(identifier,allowed[identifier][0])} for identifier in ids)
        self.delete_verified_points(targets)

    def scroll_points(self, project_id: str) -> List[Dict[str, Any]]:
        points=[]
        offset=None
        deadline=time.monotonic()+30
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0 or len(points)>=10000:
                raise ValueError('KNOWLEDGE_AUDIT_BOUND_EXCEEDED')
            body={'filter':{'must':[{'key':'project_id','match':{'value':str(project_id)}}]},
                'limit':256,'with_payload':True,'with_vector':False}
            if offset is not None:
                body['offset']=offset
            response=self._http.post(f'{self.qdrant_url}/collections/{self.collection_name}/points/scroll',
                json=body,timeout=min(10,remaining))
            response.raise_for_status()
            result=response.json()['result']
            points.extend(result['points'])
            offset=result['next_page_offset']
            if offset is None:
                return points

    def delete_stale_points(self, source_id: str, project_id: str, doc_type: str, keep_ids: List[str]) -> bool:
        """Prune only this typed source after its replacement points have been verified."""
        body = {'filter': {'must': [
            {'key': 'source_id', 'match': {'value': source_id}},
            {'key': 'project_id', 'match': {'value': project_id}},
            {'key': 'doc_type', 'match': {'value': doc_type}}],
            'must_not': [{'has_id': keep_ids}] if keep_ids else []}}
        try:
            ensure_current()
            response = self._http.post(f"{self.qdrant_url}/collections/{self.collection_name}/points/delete",
                params={'wait': 'true'}, json=body, timeout=10.0)
            return response.status_code == 200 and response.json().get('result', {}).get('status') == 'completed'
        except (httpx.HTTPError, ValueError, TypeError):
            return False

    def search_dense(
        self,
        query_vector: List[float],
        project_id: str,
        role: str,
        limit: int = 10,
        doc_types: Optional[List[str]] = None,
        actor_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Dense similarity search in Qdrant with role & project ACL pre-filtering."""
        if not self.enabled:
            return []
        try:
            must_filters: List[Dict[str, Any]] = [
                {"key": "project_id", "match": {"value": str(project_id)}},
            ]
            if role == 'AI_SYSTEM_OWNER':
                if document_ids is None:
                    raise PermissionError('OWNER_NATIVE_DOCUMENT_SCOPE_REQUIRED')
            else:
                must_filters.append({"key": "allowed_roles", "match": {"value": role}})
            if doc_types:
                must_filters.append({"key": "doc_type", "match": {"any": doc_types}})
            if document_ids is not None:
                if not document_ids:
                    return []
                must_filters.append({'key':'document_id','match':{'any':document_ids}})
            elif actor_id is not None:
                must_filters.append({"key": "actor_id", "match": {"value": actor_id}})

            body = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "filter": {
                    "must": must_filters
                },
            }
            url = f"{self.qdrant_url}/collections/{self.collection_name}/points/search"
            res = self._http.post(url, json=body, timeout=10.0)
            if res.status_code != 200:
                raise RuntimeError(f'QDRANT_SEARCH_HTTP_{res.status_code}')
            data = res.json()
            return data.get("result", [])
        except Exception as e:
            logger.error('Qdrant dense search failed: %s',type(e).__name__)
            raise
