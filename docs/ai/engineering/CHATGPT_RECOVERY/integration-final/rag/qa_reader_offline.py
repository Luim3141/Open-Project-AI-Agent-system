"""CPU1, bounded-memory extractive reader experiment. Not a production module."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from download_qa_reader import ASSETS, REPOSITORY, REVISION
from qa_span_decode import decode_span

assert int(Path('/sys/fs/cgroup/memory.max').read_text()) <= 1280 * 1024 * 1024
for name, (expected, size) in ASSETS.items():
    path = Path('/model') / name
    assert path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == expected
ort.disable_telemetry_events()
options = ort.SessionOptions()
options.intra_op_num_threads = options.inter_op_num_threads = 1
options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
options.add_session_config_entry('session.intra_op.allow_spinning', '0')
begin = time.monotonic()
tokenizer = Tokenizer.from_file('/model/tokenizer.json')
tokenizer.no_padding()
tokenizer.enable_truncation(max_length=384, strategy='only_second')
session = ort.InferenceSession('/model/onnx/model_quantized.onnx', sess_options=options, providers=['CPUExecutionProvider'])
loaded = time.monotonic()
names = [item.name for item in session.get_inputs()]
batch = json.loads(Path('/data/pairs.json').read_text(encoding='utf-8'))
assert 1 <= len(batch['pairs']) <= 400
rows = []
for pair in batch['pairs']:
    assert isinstance(pair['query'], str) and len(pair['query']) <= 1000
    assert isinstance(pair['passage'], str) and len(pair['passage']) <= 8000
    start = time.monotonic()
    encoding = tokenizer.encode(pair['query'], pair['passage'])
    truncated = bool(encoding.overflowing)
    feed = {'input_ids': np.array([encoding.ids], dtype=np.int64),
            'attention_mask': np.array([encoding.attention_mask], dtype=np.int64),
            'token_type_ids': np.array([encoding.type_ids], dtype=np.int64)}
    output = session.run(None, {name: feed[name] for name in names})
    assert len(output) == 2
    answer = None if truncated else decode_span(pair['passage'], encoding.offsets, encoding.sequence_ids,
                                               np.asarray(output[0]).reshape(-1).tolist(), np.asarray(output[1]).reshape(-1).tolist())
    elapsed = time.monotonic() - start
    if elapsed > 5:
        raise TimeoutError('QA_SINGLE_PASSAGE_CPU_BUDGET_EXCEEDED')
    rows.append({'id': pair['id'], 'answer': answer, 'seconds': elapsed, 'truncated': truncated, 'tokens': len(encoding.ids)})
result = {'repository': REPOSITORY, 'revision': REVISION, 'null_margin': 0, 'max_answer_tokens': 64,
          'max_context_tokens': 384, 'model_load_seconds': loaded - begin, 'total_seconds': time.monotonic() - begin,
          'cgroup_memory_peak': int(Path('/sys/fs/cgroup/memory.peak').read_text()), 'rows': rows,
          'input_sha256': hashlib.sha256(Path('/data/pairs.json').read_bytes()).hexdigest(), 'network': 'none', 'cpu_threads': 1}
Path('/output/scores.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
