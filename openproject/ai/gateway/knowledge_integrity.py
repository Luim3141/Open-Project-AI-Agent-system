"""Read-only reconciliation by provenance, version and exact chunk identity; never prunes data."""
import hashlib
from pathlib import Path

from .knowledge_classifier import _compute_hash
from .knowledge_lock import lease
from .knowledge_storage import KnowledgeStorage,KnowledgeStorageConfig


def reconcile(root, project, native_items, vector):
    path=Path(root)/'knowledge.sqlite'
    with lease(str(path)+'.ingest.lock'):
        storage=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(path)))
        docs={d.source_hash:d for d in storage.query_documents(str(project))}
        native={item['id']:item for item in native_items}
        chunks=[c for c in storage._mock_tables[f'{storage.schema_name}.knowledge_chunks'].values() if c['document_id'] in docs]
        expected={}
        invalid_chunks=[]
        for chunk in chunks:
            doc=docs[chunk['document_id']]
            payload={'document_id':doc.source_hash,'source_id':doc.source_id,'project_id':doc.project_id,
                'doc_type':doc.doc_type.value,'title':doc.title,'chunk_index':chunk['chunk_index'],
                'chunk_text':chunk['chunk_text'],'chunk_hash':chunk['chunk_hash'],'allowed_roles':doc.allowed_roles,'metadata':doc.metadata}
            if 'native_id' in doc.metadata:
                payload['work_package_id']=doc.metadata['native_id']
            if 'actor_id' in doc.metadata:
                payload['actor_id']=doc.metadata['actor_id']
            identifier=vector.deterministic_uuid(f"{doc.source_hash}:{chunk['chunk_index']}")
            expected[identifier]=payload
            if hashlib.sha256(f"{chunk['chunk_index']}:{chunk['chunk_text']}".encode()).hexdigest()!=chunk['chunk_hash']:
                invalid_chunks.append(identifier)
        points=vector.scroll_points(str(project))
        actual={str(point['id']):point['payload'] for point in points}
        missing=sorted(set(expected)-set(actual))
        unmatched=sorted(set(actual)-set(expected))
        mismatched=sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])
        hash_errors=[d.source_id for d in docs.values() if
            _compute_hash(d.content,d.doc_type.value,d.source_id,d.project_id)!=d.source_hash]
        stale=[]
        indexed=set()
        namespaces={}
        for doc in docs.values():
            identifier=doc.metadata.get('native_id')
            if type(identifier) is int:
                namespaces.setdefault(identifier,[]).append(doc.source_id)
                if identifier in native:
                    indexed.add(identifier)
                    if doc.metadata.get('lock_version')!=native[identifier]['lockVersion']:
                        stale.append(doc.source_id)
        with storage._connection() as db:
            counts={r[0]:r[1] for r in db.execute('SELECT source_hash,count(*) FROM knowledge_fts GROUP BY source_hash')}
            quick_check=db.execute('PRAGMA quick_check').fetchone()[0]
        fts_errors=[d.source_id for d in docs.values() if counts.get(d.source_hash)!=1]
        orphan_fts_count=sum(count for source,count in counts.items() if source not in storage._mock_tables[f'{storage.schema_name}.knowledge_documents'])
        native_missing=sorted(set(native)-indexed)
        problems=bool(missing or mismatched or hash_errors or invalid_chunks or stale or fts_errors or orphan_fts_count or native_missing or quick_check!='ok')
        return {'status':'DRIFT_DETECTED' if problems else 'PARTIAL_UNMATCHED_POINTS' if unmatched else 'VERIFIED',
            'project_id':project,'native_visible_packages':len(native),'documents':len(docs),'chunks':len(chunks),
            'points_in_project':len(points),'sqlite_quick_check':quick_check,
            'missing_native_ids':native_missing,'missing_point_ids':missing,'payload_mismatch_ids':mismatched,
            'invalid_chunk_hash_ids':invalid_chunks,'invalid_source_hashes':hash_errors,'fts_error_sources':fts_errors,
            'orphan_fts_rows':orphan_fts_count,
            'stale_sources':sorted(stale),'unmatched_points':[{'id':k,'source_id':actual[k].get('source_id')} for k in unmatched],
            'multiple_namespaces':{str(k):sorted(v) for k,v in namespaces.items() if len(v)>1},
            'native_sources_outside_visible_scope':sum(k not in native for k in namespaces),
            'mutations_performed':False,'cross_store_snapshot':'Main ingestion lease; external writers must honor the same lock'}
