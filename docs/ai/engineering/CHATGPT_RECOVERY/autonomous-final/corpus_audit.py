"""Read-only MAIN corpus audit; private immutable SQLite copy, public counts only."""
import collections,datetime,hashlib,json,os,re,sqlite3,subprocess,sys
from pathlib import Path

OUT=Path(__file__).parent
RAG=OUT.parent/'integration-final/rag';sys.path.insert(0,str(RAG))
from source_spans import extract_spans,_FIELDS,_json_end

private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/autonomous-final'
private.mkdir(exist_ok=True,parents=True)
snapshot=private/'knowledge-baseline.sqlite'
if not snapshot.exists():
    code="import sqlite3,sys;s=sqlite3.connect('file:/state/knowledge.sqlite?mode=ro',uri=True);d=sqlite3.connect(':memory:');s.backup(d);sys.stdout.buffer.write(d.serialize())"
    raw=subprocess.check_output(['docker','exec','qldapm-ai-gateway-1','python','-c',code],timeout=45)
    with snapshot.open('xb') as stream:stream.write(raw)
db=sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
fields=collections.Counter();omitted=collections.Counter();duplicates=collections.Counter();rows=[]
def strings(value,path=()):
    if isinstance(value,dict):
        for key,item in value.items():yield from strings(item,path+(key,))
    elif isinstance(value,list):
        for item in value:yield from strings(item,path)
    elif isinstance(value,str):yield path,value
for doc in db.execute("SELECT * FROM knowledge_documents WHERE project_id='6' AND source_id LIKE 'actor:20:wp:%' ORDER BY source_id"):
    text=doc['content'];meta=json.loads(doc['metadata']);spans=extract_spans(text)
    complete=0;truncated=0;tail=0
    for match in re.finditer(r'(?m)^\s*(?:Bình luận #\d+: )?([\[{])',text):
        start=match.start(1);end=_json_end(text,start,128000)
        if end is None:
            truncated+=1;tail=max(tail,len(text)-start);continue
        try:value=json.loads(text[start:end])
        except ValueError:continue
        complete+=1
        for path,value in strings(value):
            field=path[-1] if path else ''
            fields[field]+=1
            if len(value.strip())>=20:
                duplicates[hashlib.sha256(value.encode()).hexdigest()]+=1
                if field not in _FIELDS and not re.search('password|secret|token|credential|key|authorization',str(path),re.I):omitted[field]+=1
    rows.append({'native_id':meta.get('native_id'),'version':meta.get('lock_version'),'document_id':doc['source_hash'],
        'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'chars':len(text),'spans':len(spans),
        'represented_chars':sum(s['end']-s['start'] for s in spans),'complete_json_blocks':complete,
        'incomplete_json_starts':truncated,'tail_after_incomplete_json_chars':tail,
        'comments_at_750_char_limit':sum(len(c)==750 for c in re.findall(r'(?m)^Bình luận #\d+: (.*)$',text))})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'read-only MAIN knowledge.sqlite snapshot',
    'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'actor':20,'project':6,'documents':len(rows),
    'chars':sum(r['chars'] for r in rows),'represented_chars':sum(r['represented_chars'] for r in rows),
    'documents_with_incomplete_json':sum(bool(r['incomplete_json_starts']) for r in rows),
    'comments_at_750_char_limit':sum(r['comments_at_750_char_limit'] for r in rows),
    'omitted_string_fields':dict(omitted.most_common()),'json_string_fields':dict(fields.most_common()),
    'repeated_string_values':sum(n>1 for n in duplicates.values()),'repeated_string_occurrences':sum(n-1 for n in duplicates.values()),
    'rows':rows,'holdout_access':False,'main_changed':False,
    'limits':['Incomplete JSON starts are structural observations, not proof every tail is answer evidence.',
              'The existing extractor stops at an incomplete unprefixed JSON block; prefixed comments are treated as plaintext.',
              'Snapshot labels/counts do not constitute human ground truth or current Native authorization.']}
(OUT/'rag-corpus-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
