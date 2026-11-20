"""Preserve the failed frozen candidate and restore the serving retrieval source."""
import hashlib,json,subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[6]
out=Path(__file__).parent
archive=out/'rejected-candidate'
archive.mkdir(exist_ok=True)
lock=json.loads((out/'candidate-lock.json').read_text())
for rel,sha in lock['source'].items():
    source=root/rel
    destination=archive/source.name
    if not destination.exists():
        assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
        destination.write_bytes(source.read_bytes())
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==sha
source=root/'openproject/ai/gateway/knowledge_search.py'
subprocess.run(['docker','cp','qldapm-ai-gateway-1:/app/gateway/knowledge_search.py',str(source)],check=True,capture_output=True)
service=root/'openproject/ai/gateway/service.py'
text=service.read_text(encoding='utf-8')
text=text.replace("KnowledgeSearchEngine(storage,vector_client=vector,hybrid_evidence=self.config.get('demo_hybrid_rag') is True)","KnowledgeSearchEngine(storage,vector_client=vector)")
service.write_text(text,encoding='utf-8')
result=json.loads((out/'holdout-result.json').read_text())
assert result['metrics']['candidate']['false_positive_rate']>.05
(out/'disposition.json').write_text(json.dumps({'status':'REJECTED_NOT_DEPLOYED','holdout':result['metrics'],
    'restored_knowledge_search_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'labels':'SOURCE_GROUNDED_AGENT_LABELS_HUMAN_REVIEW_PENDING','further_holdout_tuning':False},indent=2)+'\n')
info=subprocess.run(['docker','inspect','qldapm-demo-rag-evaluation'],capture_output=True)
if info.returncode==0:
    assert json.loads(info.stdout)[0]['Config']['Labels'].get('org.qldapm.demo-rag')=='true'
    subprocess.run(['docker','rm','-f','qldapm-demo-rag-evaluation'],check=True,capture_output=True)
print('REJECTED candidate archived; serving retrieval restored; owned evaluation container removed')
