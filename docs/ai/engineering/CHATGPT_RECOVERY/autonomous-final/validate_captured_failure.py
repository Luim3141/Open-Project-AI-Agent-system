"""Offline only: classify saved diagnostic response, without inference or replay."""
import hashlib,json,os,sys
from pathlib import Path
OUT=Path(__file__).parent;RAG=OUT.parent/'integration-final/rag';sys.path.insert(0,str(RAG))
from source_spans import extract_spans
from evidence_validation import EvidenceError,validate_response,repair_span_reference

private=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/integration-final-rag-dev'
packet=json.loads((private/'short-context-pilot/input.json').read_text(encoding='utf-8'))['packets'][2]
capture=json.loads((private/'autonomous-grouped-failure-diagnostic/response-redacted.json').read_text())
reply=json.loads(capture['redacted_preview']);content=reply['message']['content']
raw=json.dumps(content,ensure_ascii=False) if isinstance(content,dict) else content
sources={};spans={}
for item in json.loads((RAG/'eval/native-source-manifest.json').read_text(encoding='utf-8'))['documents']:
    path=RAG/'eval/private'/item['snapshot_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['snapshot_sha256']
    text=path.read_text(encoding='utf-8');sources[item['source_hash']]=text
    for span in extract_spans(text):spans[(item['source_hash'],span['start'],span['end'])]=span
try:validate_response(raw,packet,sources,spans);raise AssertionError('Expected wrong span')
except EvidenceError as error:diagnostic=error.diagnostic();assert error.rule=='SPAN_REFERENCE_MISMATCH'
fixed,audit=repair_span_reference(raw,packet,sources,spans);rows=validate_response(fixed,packet,sources,spans)
assert rows[0]['support']=='UNVERIFIED'
result={'mode':'OFFLINE_SAVED_RESPONSE_ONLY','diagnostic':diagnostic,'deterministic_pointer_repair':audit,
        'citation_identity_valid':True,'answer_support':'UNSUPPORTED_BY_SOURCE_REVIEW',
        'reason':'Preserving old mapping/results does not entail restoring Native history; another same-source span explicitly says NEW record, not restoration.',
        'semantic_review_provenance':'assistant source inspection, not human truth label','model_calls':0,'main_changed':False}
(OUT/'rag-grouped-offline-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
