"""Download pinned public QA weights only; never send project data to a provider."""
import hashlib
import json
import os
import urllib.request
from pathlib import Path

REPOSITORY = 'onnx-community/xlm-roberta-base-finetuned-squad2-ONNX'
REVISION = '00e1042302c6444d04fea71f5785a539b599ad73'
ASSETS = {
    'onnx/model_quantized.onnx': ('1151c90ed8b2e975145825c8243ff773c49cdf11d601ece367dad791f4701853', 278655644),
    'tokenizer.json': ('e9092d8b5989337626af7001a7a97b88471e2da7c59dce83aba82a0ef90cad1f', 17082999),
}

if __name__ == '__main__':
    target = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/integration-final-qa-reader/assets'
    for name, (expected, size) in ASSETS.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            partial = path.with_suffix('.partial')
            with urllib.request.urlopen(f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}', timeout=120) as response, partial.open('wb') as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
            with partial.open('rb') as stream:
                assert partial.stat().st_size == size and hashlib.file_digest(stream, 'sha256').hexdigest() == expected
            partial.replace(path)
        with path.open('rb') as stream:
            assert path.stat().st_size == size and hashlib.file_digest(stream, 'sha256').hexdigest() == expected
    print(json.dumps({'repository': REPOSITORY, 'revision': REVISION, 'bytes': sum(size for _, size in ASSETS.values()),
                      'base_model': 'IProject-10/xlm-roberta-base-finetuned-squad2', 'base_license': 'MIT', 'scope': 'PUBLIC_ASSETS_ONLY'}))
