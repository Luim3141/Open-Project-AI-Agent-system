"""Final bounded negative RAG read and live source/control preservation proofs."""
import json,runpy,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
# Importing the fixed smoke runs its read-only assertions before the extra answer case.
from main_read import command
query='What exact coffee budget on Mars is documented by ORBIT-RECEIPT-20261103?'
status,packet=command('knowledge_search',{'query':query,'mode':'answer','limit':5})
result=packet.get('result',{})
checks={'http':status==200,'actual_model_abstention':result.get('model_used') is True and result.get('answer') is None and result.get('answerability',{}).get('state')=='ABSTAIN','exact_model':result.get('generation',{}).get('resolved_model_version')=='gemini-3.5-flash-lite'}
(OUT/'main-negative-answer.json').write_text(json.dumps({'query':query,'checks':checks,'packet':packet},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks));assert all(checks.values())
