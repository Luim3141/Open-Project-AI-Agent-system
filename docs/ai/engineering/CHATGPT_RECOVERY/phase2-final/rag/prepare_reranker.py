"""Download only official immutable assets; hash verified; no model import/inference."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import httpx

revision='1427fd652930e4ba29e8149678df786c240d8825'
metadata=json.loads(Path(__file__).with_name('reranker-metadata.json').read_text())
cache=Path(os.environ['LOCALAPPDATA'])/'QLDAPM/openproject-ai/operator/phase2-reranker'
assets=cache/'assets';assets.mkdir(parents=True,exist_ok=True)
names=['onnx/model_quint8_avx2.onnx','tokenizer.json','tokenizer_config.json','special_tokens_map.json','config.json']
files={f['rfilename']:f for f in metadata['files']}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
records=[]
with httpx.Client(follow_redirects=True,timeout=60) as client:
    for name in names:
        info=files[name];target=assets/name;target.parent.mkdir(parents=True,exist_ok=True)
        expected=(info.get('lfs') or {}).get('sha256')
        if not target.exists():
            temporary=target.with_suffix(target.suffix+'.partial')
            url=f'https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1/resolve/{revision}/{name}'
            with client.stream('GET',url) as response:
                response.raise_for_status()
                with temporary.open('wb') as stream:
                    for chunk in response.iter_bytes(1024*1024):stream.write(chunk)
            assert temporary.stat().st_size==info['size'],name
            assert expected is None or sha(temporary)==expected,name
            temporary.replace(target)
        assert target.stat().st_size==info['size'],name
        digest=sha(target);assert expected is None or digest==expected,name
        records.append({'name':name,'size':target.stat().st_size,'sha256':digest,'publisher_lfs_sha256':expected})
        print(name,target.stat().st_size,'VERIFIED',flush=True)
    license_response=client.get(f'https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1/raw/{revision}/README.md')
    license_response.raise_for_status();assert 'license: apache-2.0' in license_response.text
    (assets/'README.md').write_text(license_response.text,encoding='utf-8')
manifest={'utc':datetime.now(timezone.utc).isoformat(),'revision':revision,'license':'Apache-2.0 model card',
    'source':'official cross-encoder publisher repository, immutable commit','assets':records,
    'total_bytes':sum(f['size'] for f in records),'inference_performed':False}
(cache/'asset-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
