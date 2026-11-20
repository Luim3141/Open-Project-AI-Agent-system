"""Diagnosis on already observed DEV only; fixed top-two spans/document and null>span rule.

Reuses frozen retrieval/reranker scores; therefore timings are lower bounds, not E2E.
Never opens holdout questions or labels. Project passages/answers stay in operator storage.
"""
import hashlib
import json
import math
import os
import sqlite3
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent
EVAL = ROOT / 'eval'
OPERATOR = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator'
OLD = OPERATOR / 'integration-final-rag-dev/span-reranker8'
WORK = OPERATOR / 'integration-final-qa-reader/dev-top2'
DATA, OUTPUT = WORK / 'input', WORK / 'output'
sha = lambda value: hashlib.sha256(value).hexdigest()
plan = json.loads((EVAL / 'evaluation-plan.json').read_text())
assert sha((EVAL / 'dev.json').read_bytes()) == plan['dev_sha256']
assert sha((EVAL / 'native-source-manifest.json').read_bytes()) == plan['source_manifest_sha256']
cases = json.loads((EVAL / 'dev.json').read_text(encoding='utf-8'))['cases']
manifest = json.loads((EVAL / 'native-source-manifest.json').read_text(encoding='utf-8'))
sources = {}
with sqlite3.connect((OPERATOR / 'integration-final-rag-dev/knowledge.sqlite').as_uri() + '?mode=ro', uri=True) as db:
    for doc in manifest['documents']:
        path = EVAL / 'private' / doc['snapshot_file']
        assert sha(path.read_bytes()) == doc['snapshot_sha256']
        content = path.read_text(encoding='utf-8')
        row = db.execute('SELECT content,metadata,project_id,allowed_roles FROM knowledge_documents WHERE source_hash=? AND source_id=?', (doc['source_hash'], doc['source_id'])).fetchone()
        assert row and row[0] == content and json.loads(row[1]) == doc['metadata'] and row[2] == '6' and json.loads(row[3]) == doc['roles']
        assert doc['metadata']['actor_id'] == 20 and 'PM' in doc['roles']
        sources[doc['source_hash']] = content
metadata = json.loads((OLD / 'candidates.json').read_text())
assert metadata['dev_sha256'] == plan['dev_sha256']
original_pairs = {pair['id']: pair for pair in json.loads((OLD / 'pairs.json').read_text(encoding='utf-8'))['pairs']}
scores = {}
for path in sorted(OLD.glob('batch-*/output/scores.json')):
    report = json.loads(path.read_text())
    scores.update({row['id']: row for row in report['rows']})
assert len(scores) == len(original_pairs)
selected, records = [], []
for case, row in zip(cases, metadata['metadata'], strict=True):
    assert case['id'] == row['case']
    counts = {}
    chosen = []
    for candidate in sorted(row['candidates'], key=lambda value: -scores[value['pair_id']]['score']):
        native = candidate['native_id']
        if counts.get(native, 0) == 2 or scores[candidate['pair_id']]['truncated']:
            continue
        counts[native] = counts.get(native, 0) + 1
        pair = original_pairs[candidate['pair_id']]
        content = sources[candidate['document_id']]
        assert pair['query'] == case['query'] and content[candidate['start']:candidate['end']] == pair['passage']
        assert sha(pair['passage'].encode()) == candidate['span_sha256'] and sha(content.encode()) == candidate['source_sha256']
        selected.append(pair)
        chosen.append(candidate)
    records.append({'case': case['id'], 'chosen': chosen,
                    'previous_seconds': row['embedding_and_retrieval_seconds'] + row['selection_seconds'] + sum(scores[c['pair_id']]['seconds'] for c in row['candidates'])})
assert len(selected) <= 400
DATA.mkdir(parents=True, exist_ok=False)
OUTPUT.mkdir()
(DATA / 'pairs.json').write_text(json.dumps({'pairs': selected}, ensure_ascii=False), encoding='utf-8')
(WORK / 'candidates.json').write_text(json.dumps(records), encoding='utf-8')
mount = lambda source, target, ro=True: ['--mount', f'type=bind,source={source.resolve()},target={target}' + (',readonly' if ro else '')]
command = ['docker', 'run', '--rm', '--network', 'none', '--cpus', '1', '--memory', '1280m']
command += mount(OPERATOR / 'integration-final-qa-reader/assets', '/model') + mount(OPERATOR / 'phase2-reranker/venv', '/experiment/venv')
command += mount(ROOT, '/src') + mount(DATA, '/data') + mount(OUTPUT, '/output', False)
command += ['--entrypoint', '/experiment/venv/bin/python', 'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb', '/src/qa_reader_offline.py']
begin = time.monotonic()
run = subprocess.run(command, capture_output=True, timeout=180)
if run.returncode:
    raise RuntimeError('QA_DEV_DIAGNOSIS_FAILED: ' + run.stderr.decode(errors='replace')[-1000:])
result = json.loads((OUTPUT / 'scores.json').read_text(encoding='utf-8'))
qa = {row['id']: row for row in result['rows']}
rows = []
for case, record in zip(cases, records, strict=True):
    answers = [candidate for candidate in record['chosen'] if qa[candidate['pair_id']]['answer'] is not None]
    answers.sort(key=lambda candidate: -qa[candidate['pair_id']]['answer']['margin'])
    hits = []
    for candidate in answers:
        if candidate['native_id'] not in [hit['native_id'] for hit in hits]:
            hits.append(candidate)
    hits = hits[:5]
    rank = next((index + 1 for index, hit in enumerate(hits) if hit['native_id'] in case['relevant_ids']), None)
    support_start = case.get('support_offset', -1)
    support_end = support_start + len(case.get('support_literal', ''))
    support = any(hit['native_id'] in case['relevant_ids'] and hit['start'] <= support_start and hit['end'] >= support_end for hit in hits)
    rows.append({'case': case['id'], 'kind': case['kind'], 'language': case['language'], 'rank': rank,
                 'support_span_contained': support, 'ids': [hit['native_id'] for hit in hits],
                 'seconds_lower_bound': record['previous_seconds'] + sum(qa[c['pair_id']]['seconds'] for c in record['chosen']),
                 'answers_returned': len(hits)})
positive = [row for row in rows if row['kind'] == 'positive']
negative = [row for row in rows if row['kind'] == 'negative']
times = sorted(row['seconds_lower_bound'] for row in rows[1:])
public = {'status': 'OBSERVED_DEV_DIAGNOSIS_NOT_ACCEPTANCE', 'dev_sha256': plan['dev_sha256'],
          'reader_sha256': sha((ROOT / 'qa_reader_offline.py').read_bytes()), 'decoder_sha256': sha((ROOT / 'qa_span_decode.py').read_bytes()),
          'model_revision': result['revision'], 'selector': 'top2 nontruncated reranker spans per retrieved document; at most5documents',
          'null_margin': 0, 'pairs': len(selected), 'positive': len(positive), 'negative': len(negative),
          'document_hit5': sum(row['rank'] is not None for row in positive),
          'support_span_hit5': sum(row['support_span_contained'] for row in positive),
          'false_positive_count': sum(bool(row['answers_returned']) for row in negative),
          'hit_at_5': sum(row['rank'] is not None for row in positive) / len(positive),
          'false_positive_rate': sum(bool(row['answers_returned']) for row in negative) / len(negative),
          'warm_p95_lower_bound_seconds': times[math.ceil(0.95 * len(times)) - 1], 'peak_memory_bytes': result['cgroup_memory_peak'],
          'reader_model_load_seconds': result['model_load_seconds'], 'container_wall_seconds': time.monotonic() - begin,
          'citation_span_identity_errors': 0, 'rows': rows,
          'limitations': ['previously observed dev and correlated VN/EN pairs', 'labels author-reviewed, not independent/human adjudication',
                          'cached frozen retrieval/reranking; summed lower-bound timings exclude IPC/concurrency',
                          'raw extracted strings are not assessed as a complete answer; literal support containment is reported separately',
                          'no MAIN writes, no heldout questions/labels opened, no live ACL/freshness qualification']}
(ROOT / 'qa-reader-dev.json').write_text(json.dumps(public, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in public.items() if key != 'rows'}))
