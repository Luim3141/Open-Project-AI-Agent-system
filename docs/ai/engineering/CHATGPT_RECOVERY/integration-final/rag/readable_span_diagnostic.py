"""Static observed-DEV normalization/coverage diagnostic; no model/API/holdout calls."""
import hashlib
import json
import os
from pathlib import Path

from readable_spans import readable_span
from source_spans import extract_spans

ROOT = Path(__file__).parent
PRIVATE = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/integration-final-rag-dev/span-reranker8'
sha = lambda value: hashlib.sha256(value).hexdigest()
plan = json.loads((ROOT / 'eval/evaluation-plan.json').read_text())
assert sha((ROOT / 'eval/dev.json').read_bytes()) == plan['dev_sha256']
assert sha((ROOT / 'eval/native-source-manifest.json').read_bytes()) == plan['source_manifest_sha256']
cases = json.loads((ROOT / 'eval/dev.json').read_text(encoding='utf-8'))['cases']
manifest = json.loads((ROOT / 'eval/native-source-manifest.json').read_text(encoding='utf-8'))
sources = {}
views = {}
totals = {'spans': 0, 'changed_spans': 0, 'raw_chars': 0, 'readable_chars': 0, 'duplicate_readable_spans': 0}
for document in manifest['documents']:
    path = ROOT / 'eval/private' / document['snapshot_file']
    assert sha(path.read_bytes()) == document['snapshot_sha256']
    source = path.read_text(encoding='utf-8')
    sources[document['source_hash']] = source
    seen = set()
    for span in extract_spans(source):
        view = readable_span(source, span)
        views[(document['source_hash'], view['start'], view['end'])] = view
        totals['spans'] += 1
        totals['changed_spans'] += view['raw'] != view['readable']
        totals['raw_chars'] += len(view['raw'])
        totals['readable_chars'] += len(view['readable'])
        totals['duplicate_readable_spans'] += view['readable'] in seen
        seen.add(view['readable'])
metadata = json.loads((PRIVATE / 'candidates.json').read_text())
assert metadata['dev_sha256'] == plan['dev_sha256']
scores = {}
for path in sorted(PRIVATE.glob('batch-*/output/scores.json')):
    scores.update({row['id']: row for row in json.loads(path.read_text())['rows']})
rows = []
for case, record in zip(cases, metadata['metadata'], strict=True):
    assert case['id'] == record['case']
    grouped = {native: [] for native in record['retrieved_native_ids']}
    seen = {native: set() for native in grouped}
    for candidate in sorted(record['candidates'], key=lambda value: -scores[value['pair_id']]['score']):
        native = candidate['native_id']
        view = views[(candidate['document_id'], candidate['start'], candidate['end'])]
        if scores[candidate['pair_id']]['truncated'] or not view['readable'] or view['readable'] in seen[native]:
            continue
        seen[native].add(view['readable'])
        grouped[native].append((candidate, view))
    # Fixed hypothesis before measuring: round-robin top3 distinct spans/document, whole spans only.
    selected = []
    budget = 6000
    for position in range(3):
        for pool in grouped.values():
            if position < len(pool):
                candidate, view = pool[position]
                size = len(view['readable'])
                if size <= budget:
                    selected.append(candidate)
                    budget -= size
    offset = case.get('support_offset', -1)
    end = offset + len(case.get('support_literal', ''))
    support = any(candidate['native_id'] in case['relevant_ids'] and candidate['start'] <= offset and candidate['end'] >= end for candidate in selected)
    rows.append({'case': case['id'], 'kind': case['kind'], 'selected_spans': len(selected), 'readable_chars': 6000 - budget,
                 'literal_support_in_context': support})
result = {'status': 'STATIC_DIAGNOSTIC_ONLY_NO_INFERENCE', 'dev_sha256': plan['dev_sha256'],
          'normalizer_sha256': sha((ROOT / 'readable_spans.py').read_bytes()), 'totals': totals,
          'selector': 'cached DEV8 ranking; top3 distinct readable spans/document; roundrobin5documents; whole spans under6000chars',
          'positive': sum(row['kind'] == 'positive' for row in rows),
          'positive_literal_support_context': sum(row['literal_support_in_context'] for row in rows if row['kind'] == 'positive'),
          'max_context_spans': max(row['selected_spans'] for row in rows), 'max_context_chars': max(row['readable_chars'] for row in rows),
          'rows': rows, 'model_calls': 0, 'holdout_access': False,
          'limitations': ['normalization cannot repair missing meaning or prove answerability', 'coverage is retrospective old DEV, not accuracy',
                          'JSONdecoded text only; aliases/HTMLentities/summary remain untouched', 'dedup is within source; crosssourceconflict not resolved']}
target = ROOT / 'readable-span-diagnostic.json'
assert not target.exists(), 'PRESERVE_DIAGNOSTIC'
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
