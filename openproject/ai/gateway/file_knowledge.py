"""Pinned, server-allowlisted local documents; caller input never selects host paths."""
from contextlib import closing
from dataclasses import asdict
import hashlib
from io import BytesIO
from pathlib import Path
import re
import tempfile
import zipfile

from .knowledge_classifier import classify_document
from .knowledge_ingestion import KnowledgeIngester, IngestionStatus
from .knowledge_search import KnowledgeSearchEngine
from .knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig
from .local_loaders import is_path_allowed, load_local_file
from .native import NativeError
from .permissions import AI_SYSTEM_OWNER, ROLES


def load_source(config, who, key):
    if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', key):
        raise ValueError('FILE_SOURCE_KEY_REQUIRED')
    source = config.get('file_sources', {}).get(key)
    if not isinstance(source, dict) or source.get('project_id') != config['project_id']:
        raise PermissionError('FILE_SOURCE_NOT_ALLOWED')
    roles = source.get('allowed_roles')
    if not isinstance(roles, list) or not roles or any(role not in ROLES for role in roles):
        raise PermissionError('FILE_SOURCE_NOT_ALLOWED')
    if who['role'] != AI_SYSTEM_OWNER and who['role'] not in roles:
        raise PermissionError('FILE_SOURCE_ROLE_DENIED')
    if not source.get('root') or not source.get('path'):
        raise PermissionError('FILE_SOURCE_NOT_ALLOWED')
    path, root = Path(source['path']).resolve(), Path(source['root']).resolve()
    if not is_path_allowed(path, [root]):
        raise PermissionError('FILE_SOURCE_PATH_DENIED')
    if path.suffix.lower() not in {'.txt', '.md', '.markdown', '.csv', '.json', '.docx', '.pdf'}:
        raise ValueError('FILE_FORMAT_NOT_IMPLEMENTED')
    try:
        if path.stat().st_size > 262144:
            raise ValueError('FILE_SIZE_LIMIT')
        with path.open('rb') as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError('FILE_SIZE_LIMIT')
        sha = hashlib.sha256(raw).hexdigest()
        if sha != source.get('sha256'):
            raise NativeError(409, 'FILE_SOURCE_CHECKSUM_CHANGED')
        if path.suffix.lower() == '.docx':
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                entries = archive.infolist()
                if len(entries) > 2000 or sum(entry.file_size for entry in entries) > 8388608:
                    raise ValueError('FILE_ARCHIVE_SIZE_LIMIT')
        # Parse exactly the checked bytes; a concurrent host edit cannot replace the parser input.
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory)/path.name
            snapshot.write_bytes(raw)
            loaded = load_local_file(snapshot, project_id=str(config['project_id']),
                allowed_roles=roles, allowlist_roots=[directory])
    except PermissionError:
        raise PermissionError('FILE_SOURCE_PATH_DENIED') from None
    except OSError:
        raise NativeError(503, 'FILE_SOURCE_UNAVAILABLE') from None
    except (zipfile.BadZipFile, KeyError):
        raise ValueError('FILE_PARSING_FAILED') from None
    return classify_document(loaded.doc_type, str(config['project_id']), 'file:'+key,
        loaded.title, loaded.content, allowed_roles=roles,
        metadata={'source_key':key,'source_sha256':sha,'file_name':path.name})


def execute(service, who, action, args):
    from .vector_client import VectorClient
    required = {'source_key'} | ({'query'} if action == 'knowledge_file_search' else
        {'document_id'} if action == 'knowledge_file_read' else set())
    service.keys(args, required | ({'limit','mode'} if action == 'knowledge_file_search' else set()), required)
    if action == 'knowledge_file_search' and args.get('mode','search') not in ('search','answer'):
        raise ValueError('KNOWLEDGE_MODE_SEARCH_OR_ANSWER_REQUIRED')
    if action == 'knowledge_file_search' and (not isinstance(args['query'], str) or not 1 <= len(args['query']) <= 500):
        raise ValueError('KNOWLEDGE_QUERY_1_500')
    doc = load_source(service.config, who, args['source_key'])
    storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(service.store.root/'knowledge.sqlite')))
    citation = {'source_id':doc.source_id,'document_id':doc.source_hash,
        'source_sha256':doc.metadata['source_sha256'],'file_name':doc.metadata['file_name'],
        'citation':doc.source_id+'#sha256='+doc.metadata['source_sha256']}
    if action == 'knowledge_file_read':
        if args['document_id'] != doc.source_hash:
            raise NativeError(409, 'FILE_DOCUMENT_REVISION_CHANGED')
        stored = next((d for d in storage.query_documents(doc.project_id, who['role']) if d.source_hash == doc.source_hash), None)
        if stored is None:
            raise NativeError(404, 'FILE_DOCUMENT_NOT_INDEXED')
        return {**citation, 'content':stored.content, 'model_used':False}
    with closing(VectorClient()) as vector:
        if action == 'knowledge_file_ingest':
            result = KnowledgeIngester(storage, vector).ingest(doc)
            if result.status == IngestionStatus.FAILED:
                raise NativeError(503, 'FILE_VECTOR_INDEX_PENDING')
            if load_source(service.config, who, args['source_key']).source_hash != doc.source_hash:
                raise NativeError(409, 'FILE_SOURCE_CHECKSUM_CHANGED')
            return {**asdict(result), **citation, 'model_used':False}
        engine = KnowledgeSearchEngine(storage, vector_client=vector)
        hits = engine.search(args['query'], doc.project_id, who['role'], args.get('limit',10),
            actor_id=who['user_id'], document_ids=[doc.source_hash])
        if load_source(service.config, who, args['source_key']).source_hash != doc.source_hash:
            raise NativeError(409, 'FILE_SOURCE_CHECKSUM_CHANGED')
        from .knowledge_answer import grounded_response
        items=[{**citation,'title':hit.title,'snippet':hit.snippet,'score':hit.score,'project_id':service.config['project_id'],
            'match_type':hit.match_type,'passage':hit.passage,'chunk_index':hit.chunk_index,'chunk_hash':hit.chunk_hash,
            'retrieval_reference':f'{hit.document_id}:{hit.chunk_index}:{hit.chunk_hash}'} for hit in hits if hit.document_id == doc.source_hash]
        return {**grounded_response(args['query'],items,engine.dense_state,mode=args.get('mode','search')),'items':items,
            'dense_state':engine.dense_state,'model_used':False,'scope':'PINNED_SERVER_SOURCE_AND_FRESH_ROLE'}
