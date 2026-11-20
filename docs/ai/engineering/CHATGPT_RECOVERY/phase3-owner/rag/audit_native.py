"""Diagnose consumed Native cases, never calibrate on them or touch live indexes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path.cwd() / 'openproject/ai'))
from gateway.vector_client import VectorClient

OLD = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator/phase2-reranker'
PRIVATE = OLD.parent / 'phase3-native-audit'
OUT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    started = datetime.now(timezone.utc).isoformat()
    PRIVATE.mkdir(exist_ok=True)
    source = json.loads((OLD / 'source-snapshot.json').read_text(encoding='utf-8'))
    vectors = json.loads((OLD / 'source-vectors-frozen.json').read_text())
    records = json.loads((OLD / 'holdout-candidates.json').read_text(encoding='utf-8'))
    assert sha(OLD / 'source-snapshot.json') == 'f0186c27f40ad554c8648fcb6c31178487a58d23ac783e722c9d6a279081c18e'
    assert sha(OLD / 'source-vectors-frozen.json') == records['source_vectors_sha256']
    allowed = set(records['allowed_documents'])
    docs = {d['source_hash']: d for d in source['documents'] if d['source_hash'] in allowed}
    points = [p for p in vectors if p['payload']['document_id'] in allowed]
    assert len(docs) == 8 and len(points) == 81
    cases = [row for row in records['cases'] if row['case']['kind'] == 'positive']
    cache = PRIVATE / 'consumed-query-vectors.json'
    if cache.exists():
        embeddings = json.loads(cache.read_text(encoding='utf-8'))
    else:
        embeddings = {}
    client = VectorClient(timeout=30)
    results = []
    try:
        tags = client._http.get(client.ollama_url + '/api/tags').json()
        assert any(m['digest'] == '7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab' for m in tags['models'])
        for row in cases:
            case = row['case']
            query = case['query']
            if query not in embeddings:
                response = client._http.post(client.ollama_url + '/api/embed', json={
                    'model': 'bge-m3', 'input': [query], 'truncate': False, 'options': {'num_thread': 1}})
                response.raise_for_status()
                embeddings[query] = response.json()['embeddings'][0]
                cache.write_text(json.dumps(embeddings, ensure_ascii=False), encoding='utf-8')
            q = embeddings[query]
            assert len(q) == 1024 and all(math.isfinite(x) for x in q)
            norm = math.sqrt(sum(x*x for x in q))
            ranked = sorted([{'native_id': json.loads(docs[p['payload']['document_id']]['metadata'])['native_id'],
                'chunk_index': p['payload']['chunk_index'], 'chunk_hash': p['payload']['chunk_hash'],
                'score': sum(x*y for x,y in zip(q,p['vector'])) / norm / math.sqrt(sum(x*x for x in p['vector']))}
                for p in points], key=lambda p: -p['score'])
            relevant = [p for p in ranked if p['native_id'] in case['relevant_ids']]
            best = relevant[0]
            rank = ranked.index(best) + 1
            baseline_hit = any(h['native_id'] in case['relevant_ids'] for h in row['baseline'])
            pool_has_doc = any(p['native_id'] in case['relevant_ids'] for p in row['pool'])
            if baseline_hit:
                reason = 'BASELINE_HIT'
            elif best['score'] < .65:
                reason = 'QUALIFIED_CANDIDATE_ABSENT_COSINE_FLOOR'
            elif rank > 10:
                reason = 'CANDIDATE_ABSENT_CHUNK_TOPK'
            else:
                reason = 'RANKING_OR_FUSION_MISS'
            literal = case['evidence_literal']
            supports = [d for d in docs.values() if json.loads(d['metadata'])['native_id'] in case['relevant_ids']]
            assert supports and all(literal.casefold() in (d['title']+'\n'+d['content']).casefold() for d in supports)
            results.append({'query': query, 'language': case['language'], 'intent': case['intent'],
                'native_ids': case['relevant_ids'], 'category': reason, 'answerability': 'FROZEN_SOURCE_LITERAL_PRESENT_AGENT_LABEL',
                'baseline_ids': [h['native_id'] for h in row['baseline']], 'best_relevant': best,
                'best_relevant_chunk_rank': rank, 'raw_top10_distinct_docs': len({p['native_id'] for p in ranked[:10]}),
                'reranker_pool_has_relevant_doc': pool_has_doc, 'top10_document_counts': dict(Counter(p['native_id'] for p in ranked[:10]))})
    finally:
        client.close()
    result = {'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'DIAGNOSTIC_ONLY_CONSUMED_HOLDOUT_NO_CALIBRATION', 'command': 'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase3-owner/rag/audit_native.py',
        'source_hashes': {n: sha(OLD/n) for n in ['source-snapshot.json','source-vectors-frozen.json','holdout-candidates.json','labels-frozen.json']},
        'native_scope_historical_only': records['native_scope'], 'current_acl_verified': False,
        'scope_exclusions': records['stale_snapshot_cases_excluded_before_any_scoring'],
        'category_counts': dict(Counter(r['category'] for r in results)), 'cases': results,
        'limits': 'Source-literal proxy, not human labels. Snapshot scope historical, not current Native ACL. No fresh holdout consumed. No Main source/config/index writes.'}
    (OUT/'native-miss-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'category_counts': result['category_counts'], 'scope_excluded': len(result['scope_exclusions']),
        'started_utc': started, 'ended_utc': result['ended_utc']}, indent=2))


if __name__ == '__main__':
    run()
