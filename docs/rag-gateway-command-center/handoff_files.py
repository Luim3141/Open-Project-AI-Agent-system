"""Select explicit product/test paths and direct Phase 4 evidence files only."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
product=json.loads((OUT/'final-integrity.json').read_text())['product_changed']
tests=['openproject/ai/tests/test_rag_answers.py','openproject/ai/tests/test_rag_phase4.py','openproject/ai/tests/test_owner_live_transport.js','openproject/ai/telegram-ai/tests/test_knowledge_mode.py']
source=product+tests+['architecture.md','openproject/ai/CHECKPOINT.md']
excluded={'CURRENT.md','bot-candidate.json','bot-candidate-v1.json'}
docs=[str(p.relative_to(ROOT)).replace('\\','/') for p in OUT.iterdir() if p.is_file() and p.suffix in {'.md','.py','.json','.log','.png'} and p.name not in excluded]
paths=sorted(set(source+docs))
assert len(product)==11 and all((ROOT/p).is_file() for p in paths)
assert not any('/context/' in p or '/candidate/' in p for p in paths)
(OUT/'handoff-files.json').write_text(json.dumps(paths,indent=2)+'\n')
(OUT/'source-files.json').write_text(json.dumps(source,indent=2)+'\n')
print(json.dumps({'product':len(product),'tests':len(tests),'docs':len(docs),'total':len(paths)}))
