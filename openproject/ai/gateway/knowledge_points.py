"""Registered payload proofs remain durable until their verified replacement is indexed."""
import hashlib
import json

from .knowledge_classifier import _compute_hash


def point(doc,chunk,client):
    data={'document_id':doc.source_hash,'source_id':doc.source_id,'project_id':str(doc.project_id),
        'doc_type':doc.doc_type.value,'title':doc.title,'chunk_index':chunk['chunk_index'],
        'chunk_text':chunk['chunk_text'],'chunk_hash':chunk['chunk_hash'],
        'allowed_roles':doc.allowed_roles,'metadata':doc.metadata}
    if 'native_id' in doc.metadata:data['work_package_id']=doc.metadata['native_id']
    if 'actor_id' in doc.metadata:data['actor_id']=doc.metadata['actor_id']
    return {'id':client.deterministic_uuid(f'{doc.source_hash}:{chunk["chunk_index"]}'),'payload':data}


def remember(storage,client,doc):
    scope=(doc.project_id,doc.doc_type.value,doc.source_id)
    pending=storage.pending_vector_cleanup(scope)
    chunks=storage._mock_tables[f'{storage.schema_name}.knowledge_chunks'].values()
    for registered in storage.query_documents(doc.project_id,doc_type=doc.doc_type):
        if registered.source_id!=doc.source_id:continue
        if _compute_hash(registered.content,registered.doc_type.value,registered.source_id,registered.project_id)!=registered.source_hash:
            raise ValueError('KNOWLEDGE_PRUNE_SOURCE_HASH_HOLD')
        for chunk in chunks:
            if chunk['document_id']!=registered.source_hash:continue
            if hashlib.sha256(f'{chunk["chunk_index"]}:{chunk["chunk_text"]}'.encode()).hexdigest()!=chunk['chunk_hash']:
                raise ValueError('KNOWLEDGE_PRUNE_CHUNK_HASH_HOLD')
            pending.append(point(registered,chunk,client))
    unique={json.dumps(p,sort_keys=True,separators=(',',':')):p for p in pending}
    if len(unique)>10000:raise ValueError('KNOWLEDGE_PRUNE_PLAN_BOUND_EXCEEDED')
    result=list(unique.values())
    for entry in result:
        data=entry['payload'];index=data['chunk_index']
        if ((data['project_id'],data['doc_type'],data['source_id'])!=scope or type(index) is not int or index<0 or
                entry['id']!=client.deterministic_uuid(f'{data["document_id"]}:{index}') or
                hashlib.sha256(f'{index}:{data["chunk_text"]}'.encode()).hexdigest()!=data['chunk_hash']):
            raise ValueError('KNOWLEDGE_PRUNE_PLAN_SCOPE_OR_HASH_HOLD')
    storage.save_vector_cleanup(scope,result)
    return result


def prune(storage,client,doc,plan,keep_ids):
    client.delete_registered_points(plan,keep_ids)
    storage.save_vector_cleanup((doc.project_id,doc.doc_type.value,doc.source_id),[])
