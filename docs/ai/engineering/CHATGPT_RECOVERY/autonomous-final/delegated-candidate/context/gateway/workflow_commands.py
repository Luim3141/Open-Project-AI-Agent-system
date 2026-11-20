"""Observe completed Project6 human commands; workflow callbacks never repeat the command."""
import json
import time
import uuid
import sqlite3
from contextlib import closing

from .store import canonical,digest

KINDS={'sprint_risks':'UI_RISK_COMPLETED','bug_triage':'UI_BUG_TRIAGED',
       'knowledge_file_ingest':'UI_FILE_INDEXED','wbs_draft':'UI_WBS_DRAFTED'}


def setup(db):
    db.execute('CREATE TABLE IF NOT EXISTS workflow_command_sources(id TEXT PRIMARY KEY,actor INTEGER NOT NULL,action TEXT NOT NULL,hash TEXT NOT NULL,document TEXT NOT NULL,created REAL NOT NULL)')


def _emit(store,doc,fingerprint):
    from .integration_events import enqueue
    identifier=doc['id'];result=doc['result'];action=doc['action']
    payload={'command_id':identifier,'action':action}
    if action=='bug_triage' and result.get('native_id'):
        payload['native_id']=result['native_id']
    return enqueue(store,KINDS[action],'ui-command:'+identifier,fingerprint,
                   correlation_id=identifier,payload=payload)


def publish(store):
    # A crash after source commit must not strand the observation before outbox insertion.
    with store.connect() as db:
        setup(db)
        rows=db.execute("SELECT s.* FROM workflow_command_sources s WHERE NOT EXISTS (SELECT 1 FROM integration_event_outbox o WHERE json_extract(o.document,'$.source_id')='ui-command:'||s.id) ORDER BY s.created LIMIT 20").fetchall()
    for row in rows:
        doc=json.loads(row['document'])
        if (digest(row['document'])!=row['hash'] or doc['project']!=6 or doc['actor']!=row['actor']
                or doc['actor'] not in (18,20) or doc['action']!=row['action'] or doc['action'] not in KINDS):
            raise PermissionError('WORKFLOW_COMMAND_SCOPE_DENIED')
        _emit(store,doc,row['hash'])


def record(service,actor,command,result,correlation):
    if service.config['project_id']!=6 or command.action not in KINDS:
        return
    if type(actor) is not int or actor not in (18,20):
        raise PermissionError('WORKFLOW_COMMAND_ACTOR_DENIED')
    identifier=str(uuid.UUID(correlation))
    document={'id':identifier,'actor':actor,'project':6,'action':command.action,
              'arguments':command.arguments,'result':result}
    text=canonical(document)
    if len(text.encode())>131072:
        raise ValueError('WORKFLOW_COMMAND_RESULT_TOO_LARGE')
    fingerprint=digest(text)
    with service.store.connect() as db:
        setup(db)
        db.execute('INSERT OR IGNORE INTO workflow_command_sources VALUES(?,?,?,?,?,?)',
            (identifier,actor,command.action,fingerprint,text,time.time()))
    if command.action=='sprint_risks':
        from .engineering_observability import notification
        notification(service,'risk-report:'+result['report_id'],'SPRINT_RISK_REPORT_READY',
            message='Báo cáo rủi ro Project6 đã lưu; mở đúng report để kiểm tra nguồn và phiên bản.',
            extra={'report_id':result['report_id']})
    event_id=_emit(service.store,document,fingerprint)
    return {'event_id':event_id,'state':'COMMAND_ACCEPTED','role':'N8N_OBSERVES_COMPLETED_GATEWAY_COMMAND'}


def business(service,event):
    from .engineering import scoped_service,authorized
    scoped=scoped_service(service,6);identifier=event['payload']['command_id']
    if str(uuid.UUID(identifier))!=identifier or event['source_id']!='ui-command:'+identifier:
        raise PermissionError('WORKFLOW_COMMAND_SOURCE_DENIED')
    with service.store.connect() as db:
        row=db.execute('SELECT * FROM workflow_command_sources WHERE id=?',(identifier,)).fetchone()
    if not row or row['hash']!=event['source_version'] or digest(row['document'])!=row['hash']:
        raise PermissionError('WORKFLOW_COMMAND_SOURCE_DENIED')
    doc=json.loads(row['document']);action=row['action'];result=doc['result']
    if (doc['project']!=6 or doc['actor']!=row['actor'] or row['actor'] not in (18,20)
            or event['kind']!=KINDS.get(action) or event['payload']['action']!=action):
        raise PermissionError('WORKFLOW_COMMAND_SCOPE_DENIED')
    native,who=authorized(scoped,row['actor'])
    if action=='sprint_risks':
        saved=scoped.perform(who,native,'get_report',{'id':result['report_id']})
        if saved.get('state')!='SNAPSHOT' or saved.get('source_versions_current') is not True:
            return {'state':'SUPERSEDED','command_id':identifier}
        if saved.get('sha256')!=result['report_sha256']:
            raise ValueError('WORKFLOW_REPORT_READBACK_REQUIRED')
    elif action=='bug_triage':
        if result.get('native_id'):
            current=native.package(result['native_id'])
            if current['lockVersion']!=result['native_version']:
                return {'state':'SUPERSEDED','native_id':current['id']}
    elif action=='wbs_draft':
        from .native_wbs import load
        saved=load(scoped,result['id'])
        if saved['actor']!=row['actor'] or saved['hash']!=result['hash']:
            raise ValueError('WORKFLOW_WBS_READBACK_REQUIRED')
    elif action=='knowledge_file_ingest':
        from .file_knowledge import load_source
        from .vector_client import VectorClient
        from .knowledge_ingestion import chunk_text
        from .knowledge_points import point
        from .knowledge_search import _tokenize
        source=load_source(scoped.config,who,doc['arguments']['source_key'])
        if source.source_hash!=result['document_id']:
            return {'state':'SUPERSEDED','document_id':result['document_id']}
        chunks=chunk_text(source.content)
        with closing(sqlite3.connect('file:'+str(service.store.root/'knowledge.sqlite')+'?mode=ro',uri=True)) as db:
            stored=db.execute('SELECT content FROM knowledge_documents WHERE id=? AND project_id=?',(source.source_hash,'6')).fetchone()
            actual=db.execute('SELECT chunk_index,chunk_text,chunk_hash FROM knowledge_chunks WHERE document_id=? ORDER BY chunk_index',(source.source_hash,)).fetchall()
            expected=[(c['chunk_index'],c['chunk_text'],c['chunk_hash']) for c in chunks]
            lexical=db.execute('SELECT content FROM knowledge_fts WHERE source_hash=?',(source.source_hash,)).fetchone()
        if not stored or stored[0]!=source.content or actual!=expected or not lexical or lexical[0]!=' '.join(_tokenize(source.content)):
            raise ValueError('WORKFLOW_FILE_INDEX_READBACK_REQUIRED')
        with closing(VectorClient()) as vector:
            points=[point(source,chunk,vector) for chunk in chunks]
            if not points or not vector.verify_points(points) or result.get('vector_indexed') is not True:
                raise ValueError('WORKFLOW_FILE_INDEX_READBACK_REQUIRED')
    return {'state':'COMMAND_RESULT_VERIFIED','action':action,'command_id':identifier,
            'correlation_id':identifier,'native_writes':False,'execution_owner':'GATEWAY_HUMAN_COMMAND'}
