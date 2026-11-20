"""Read-only snapshot/model probes; corpus outputs stay in private operator directory."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path.cwd() / 'openproject/ai'))
from gateway.vector_client import VectorClient

def cosine(a, b):
    return sum(x*y for x,y in zip(a,b)) / math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))

root = Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/semantic-review-20261102'
points = json.loads((root/'source-vectors.json').read_text())
client = VectorClient(timeout=60)
started = datetime.now(timezone.utc).isoformat()
try:
    model = client._http.get(client.ollama_url+'/api/tags').json()
    selected = [p for p in points if p['payload']['chunk_index']==0]
    probes = []
    for p in selected:
        t = time.monotonic()
        a,b = [client.embed_texts([p['payload']['chunk_text']])[0] for _ in range(2)]
        probes.append({'native_id':p['payload']['metadata'].get('native_id'),
            'stored_norm':math.sqrt(sum(x*x for x in p['vector'])),
            'regenerated_norm':math.sqrt(sum(x*x for x in a)),
            'stored_vs_regenerated':cosine(p['vector'],a),
            'repeat_cosine':cosine(a,b),'repeat_max_delta':max(abs(x-y) for x,y in zip(a,b)),
            'seconds':time.monotonic()-t})
    result={'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
        'environment':'Windows host; copied historical Project6 snapshot; live local Ollama read-only embedding',
        'snapshot_hashes':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['knowledge.sqlite','source-vectors.json']},
        'models':model,'probes':probes}
    (root/'phase2-consistency.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
finally:
    client.close()
