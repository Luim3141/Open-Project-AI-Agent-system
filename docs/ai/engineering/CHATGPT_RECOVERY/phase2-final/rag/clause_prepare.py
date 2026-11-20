"""Capture exactly the authorized public-document allowlist, never ingest Main."""
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path.cwd();DEMO=Path('D:/AI project/QLDAPM-demo/mini-task-manager')
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-evidence-clauses'
REV='4a794e2b3d62247881fef4c0908eeeee9f043ba2'
SOURCES=[
 ('file-contract','openproject/ai/knowledge_sources/main-workflow-contract.md','dev','operational_contract_document'),
 ('adr1','docs/adr/0001-local-five-user-multi-agent.md','dev','historical_accepted_architecture'),
 ('adr2','docs/adr/0002-n8n-community-local-owner.md','dev','historical_accepted_architecture'),
 ('adr3','docs/adr/0003-orchestration-typed-state-machine.md','holdout','historical_accepted_architecture'),
 ('adr4','docs/adr/0004-user-capacity-scale-20.md','holdout','historical_accepted_capacity_design_not_live_capacity_proof'),
 ('ingestion','docs/ai/03_RAG_INGESTION.md','dev','historical_20261022_report_not_current_runtime_proof'),
 ('retrieval','docs/ai/04_RAG_RETRIEVAL.md','dev','historical_20261022_report_not_current_runtime_proof'),
 ('domain','docs/agents/domain.md','holdout','documented_repository_conventions_not_current_feature_acceptance'),
 ('tracker','docs/agents/issue-tracker.md','holdout','historical_tracker_operations_rules_not_current_roles_or_activation'),
 ('triage','docs/agents/triage-labels.md','holdout','documented_triage_label_contract'),
 ('demo-readme','README.md','dev','PR9_repository_README_at_commit_not_deployed_behavior'),
 ('demo-api','task_manager/app.py','holdout','implemented_source_at_PR9_commit_not_deployed_behavior'),
]
PRIVATE.mkdir(exist_ok=True);(PRIVATE/'sources').mkdir(exist_ok=True)
manifest_path=PRIVATE/'source-manifest.json';assert not manifest_path.exists(),'IMMUTABLE_MANIFEST_EXISTS'
records=[]
for key,path,split,state in SOURCES:
    demo=key.startswith('demo-')
    raw=subprocess.check_output(['git','show',f'{REV}:{path}'],cwd=DEMO) if demo else (ROOT/path).read_bytes()
    text=raw.decode('utf-8-sig');assert len(raw)<=50000
    assert not re.search(r'AIza[\w-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [^-]*PRIVATE KEY-----|(?i:password|api[_-]?key|token)\s*[:=]\s*[\"\'][A-Za-z0-9_+/=-]{20,}',text),key
    assert not re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',text,re.I),key
    sha=hashlib.sha256(raw).hexdigest();target=PRIVATE/'sources'/(key+Path(path).suffix);target.write_bytes(raw)
    records.append({'source_key':key,'origin':'REPO_FILE_NOT_NATIVE','absolute_source':str((DEMO if demo else ROOT)/path),
        'repository_relative_path':path,'raw_sha256':sha,'content_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'source_revision':REV if demo else 'sha256:'+sha,'git_committed':demo,'git_commit':REV if demo else None,
        'copy':str(target),'split':split,'classification':state,'scope':{'project_id':'6','actor_id':20,'allowed_roles':['PM']},
        'bytes':len(raw),'characters':len(text),'secret_and_email_pattern_screen':'PASS; bounded patterns, not a guarantee of every possible sensitive value'})
manifest={'frozen_utc':datetime.now(timezone.utc).isoformat(),'authorization':'Root explicit allowlist/content-addressed version approval under owner directive; clone only',
    'corpus_kind':'repo file snapshots; not Native OpenProject source','sources':records,'live_ingestion':False}
manifest_path.write_text(json.dumps(manifest,indent=2))
public=Path(__file__).with_name('clause-source-manifest.json');public.write_text(json.dumps(manifest,indent=2))
print(json.dumps({'sources':len(records),'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'frozen_utc':manifest['frozen_utc'],'source_keys':[r['source_key'] for r in records]},indent=2))
